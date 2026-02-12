import streamlit as st
import pandas as pd
from bs4 import BeautifulSoup
import pdfplumber
import base64
import re
import io

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(page_title="Accounting Expert", page_icon="logo.png", layout="wide")

# --- 2. CSS ---
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700&display=swap');
        html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
        .hero { text-align: center; padding: 40px; background: linear-gradient(135deg, #065F46, #1E40AF); color: white; border-radius: 10px; margin-bottom: 20px; }
        .stContainer { background: white; padding: 20px; border-radius: 10px; border: 1px solid #E2E8F0; }
    </style>
""", unsafe_allow_html=True)

# --- 3. LOGIC & FIXES ---

def clean_currency(value):
    if pd.isna(value) or value == '': return 0.0
    val = str(value).replace(',', '').replace('Cr', '').replace('Dr', '').strip()
    try: return float(val)
    except: return 0.0

def trace_ledger(narration, master_ledgers):
    """Priority Tracing: Longer names first to avoid partial matching."""
    if not narration or not master_ledgers: return None
    sorted_masters = sorted([str(m) for m in master_ledgers], key=len, reverse=True)
    for ledger in sorted_masters:
        if len(ledger) < 3: continue
        if re.search(r'\b' + re.escape(ledger) + r'\b', str(narration), re.IGNORECASE):
            return ledger
    return None

def smart_normalize(df):
    """Fixes the 'Empty Columns' issue by searching for headers dynamically."""
    df = df.dropna(how='all').reset_index(drop=True)
    
    # 1. Find the Header Row (Look for 'Date' and 'Balance' or 'Narration')
    header_idx = 0
    for i, row in df.iterrows():
        row_str = " ".join(row.astype(str).lower())
        if 'date' in row_str and ('balance' in row_str or 'narration' in row_str or 'particular' in row_str):
            header_idx = i
            break
    
    # 2. Re-align DataFrame
    df.columns = df.iloc[header_idx]
    df = df[header_idx + 1:].reset_index(drop=True)
    df.columns = df.columns.astype(str).str.strip().str.lower()

    # 3. Map to Tally Columns
    new_df = pd.DataFrame()
    col_map = {
        'Date': ['date', 'txn date', 'value date', 'tran date'],
        'Narration': ['narration', 'description', 'particulars', 'remarks'],
        'Debit': ['debit', 'withdrawal', 'payment', 'dr'],
        'Credit': ['credit', 'deposit', 'receipt', 'cr']
    }

    for target, aliases in col_map.items():
        for col in df.columns:
            if any(alias == col or alias in col for alias in aliases):
                new_df[target] = df[col]
                break
        if target not in new_df:
            new_df[target] = 0 if target in ['Debit', 'Credit'] else ""

    new_df['Debit'] = new_df['Debit'].apply(clean_currency)
    new_df['Credit'] = new_df['Credit'].apply(clean_currency)
    return new_df.dropna(subset=['Date'])

def generate_tally_xml(df, bank_ledger):
    """Generates Tally-compliant balanced XML."""
    xml_header = """<ENVELOPE><HEADER><TALLYREQUEST>Import Data</TALLYREQUEST></HEADER><BODY><IMPORTDATA><REQUESTDESC><REPORTNAME>Vouchers</REPORTNAME></REQUESTDESC><REQUESTDATA>"""
    xml_footer = """</REQUESTDATA></IMPORTDATA></BODY></ENVELOPE>"""
    body = ""
    for _, row in df.iterrows():
        amt = row['Debit'] if row['Debit'] > 0 else row['Credit']
        if amt <= 0: continue
        vch_type = "Payment" if row['Debit'] > 0 else "Receipt"
        
        # Tally logic: Cr is negative, Dr is positive.
        l1, l1_amt = (row['Final Ledger'], -amt) if vch_type == "Payment" else (bank_ledger, -amt)
        l2, l2_amt = (bank_ledger, amt) if vch_type == "Payment" else (row['Final Ledger'], amt)

        try: d = pd.to_datetime(row['Date'], dayfirst=True).strftime("%Y%m%d")
        except: d = "20260401" #
        
        nar = str(row['Narration']).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        
        body += f"""<TALLYMESSAGE xmlns:UDF="TallyUDF"><VOUCHER VCHTYPE="{vch_type}" ACTION="Create"><DATE>{d}</DATE><NARRATION>{nar}</NARRATION><VOUCHERTYPENAME>{vch_type}</VOUCHERTYPENAME><ALLLEDGERENTRIES.LIST><LEDGERNAME>{l1}</LEDGERNAME><ISDEEMEDPOSITIVE>{"Yes" if l1_amt < 0 else "No"}</ISDEEMEDPOSITIVE><AMOUNT>{l1_amt}</AMOUNT></ALLLEDGERENTRIES.LIST><ALLLEDGERENTRIES.LIST><LEDGERNAME>{l2}</LEDGERNAME><ISDEEMEDPOSITIVE>{"Yes" if l2_amt < 0 else "No"}</ISDEEMEDPOSITIVE><AMOUNT>{l2_amt}</AMOUNT></ALLLEDGERENTRIES.LIST></VOUCHER></TALLYMESSAGE>"""
    return xml_header + body + xml_footer

# --- 4. APP INTERFACE ---
st.markdown('<div class="hero"><h1>Accounting Expert</h1><p>Bank to Tally AI with Smart Auto-Trace</p></div>', unsafe_allow_html=True)

col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("1. Configuration")
    master_file = st.file_uploader("Upload Master.html", type=['html'])
    ledgers = ["Suspense A/c", "Cash"]
    if master_file:
        soup = BeautifulSoup(master_file, 'html.parser')
        ledgers = sorted(list(set([td.text.strip() for td in soup.find_all('td') if td.text.strip()])))
        st.success(f"{len(ledgers)} Ledgers Found")
    
    bank_ledger = st.selectbox("Bank Ledger", ledgers)
    default_party = st.selectbox("Default Party", ledgers)

with col2:
    st.subheader("2. Statement Processing")
    stmt_file = st.file_uploader("Upload Bank Statement (PDF/Excel)", type=['pdf', 'xlsx'])
    
    if stmt_file:
        with st.spinner("Processing..."):
            if stmt_file.name.endswith('.pdf'):
                with pdfplumber.open(stmt_file) as pdf:
                    data = []
                    for page in pdf.pages: data.extend(page.extract_table() or [])
                df_raw = pd.DataFrame(data)
            else:
                df_raw = pd.read_excel(stmt_file)

            if not df_raw.empty:
                df_clean = smart_normalize(df_raw)
                df_clean['Final Ledger'] = df_clean['Narration'].apply(lambda x: trace_ledger(x, ledgers) or default_party)
                
                st.write("**Data Preview (Smart Matched):**")
                st.dataframe(df_clean[['Date', 'Narration', 'Final Ledger', 'Debit', 'Credit']].head(10), use_container_width=True)
                
                if st.button("🚀 Generate Tally XML"):
                    xml = generate_tally_xml(df_clean, bank_ledger)
                    st.download_button("⬇️ Download XML", xml, "tally_import.xml", "application/xml")
