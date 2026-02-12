import streamlit as st
import pandas as pd
from bs4 import BeautifulSoup
import pdfplumber
import re
import time
import base64

# --- 1. PAGE CONFIG & ORIGINAL CSS ---
st.set_page_config(page_title="Accounting Expert | AI Bank to Tally", layout="wide")

st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700&display=swap');
        html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #F8FAFC; }
        .hero-container {
            text-align: center; padding: 50px 20px;
            background: linear-gradient(135deg, #065F46 0%, #1E40AF 100%);
            color: white; margin: -6rem -4rem 30px -4rem;
            box-shadow: 0 10px 30px -10px rgba(6, 95, 70, 0.5);
        }
        .stContainer { background-color: white; padding: 30px; border-radius: 16px; border: 1px solid #E2E8F0; }
        h3 { border-left: 5px solid #10B981; padding-left: 12px; }
        .stButton>button { 
            width: 100%; background: linear-gradient(90deg, #10B981, #3B82F6); 
            color: white; border-radius: 8px; height: 50px; font-weight: 700; border: none;
        }
    </style>
""", unsafe_allow_html=True)

# --- 2. THE PERSISTENT SIDEBAR (USER HUB) ---
with st.sidebar:
    st.title("🛡️ User Hub")
    with st.expander("👤 User Account", expanded=True):
        st.write("Logged in as: **Guest**")
    with st.expander("💳 Subscription Plans"):
        st.info("Plan: **Free Tier**")
    with st.expander("❓ Help & Solutions"):
        st.write("For 'Detection Failed', ensure PDF text is selectable.")
    st.divider()
    st.caption("Powered by Debasish Biswas")

# --- 3. REPAIRED PROCESSING LOGIC ---

def clean_currency(value):
    if pd.isna(value) or value == '': return 0.0
    val = re.sub(r'[^\d.]', '', str(value))
    try: return float(val)
    except: return 0.0

def smart_normalize(df):
    """Prevents AttributeError and finds headers by scanning for keywords."""
    if df.empty: return pd.DataFrame()
    df = df.dropna(how='all').reset_index(drop=True)
    
    header_idx = None
    for i, row in df.iterrows():
        # Force all values to string to prevent crashing
        row_str = " ".join([str(v).lower() for v in row.values if v is not None])
        if 'date' in row_str and ('narration' in row_str or 'particular' in row_str):
            header_idx = i
            break
            
    if header_idx is not None:
        df.columns = df.iloc[header_idx]
        df = df[header_idx + 1:].reset_index(drop=True)
    
    df.columns = df.columns.astype(str).str.strip().str.lower()
    new_df = pd.DataFrame()
    col_map = {
        'Date': ['date', 'txn', 'value'],
        'Narration': ['narration', 'particular', 'description'],
        'Debit': ['debit', 'withdrawal', 'dr'],
        'Credit': ['credit', 'deposit', 'cr']
    }

    for target, aliases in col_map.items():
        found = next((c for c in df.columns if any(a in c for a in aliases)), None)
        new_df[target] = df[found] if found else (0.0 if target in ['Debit', 'Credit'] else "UNTRACED")
            
    new_df['Debit'] = new_df['Debit'].apply(clean_currency)
    new_df['Credit'] = new_df['Credit'].apply(clean_currency)
    return new_df

def generate_tally_xml(df, bank_ledger):
    """Ensures balanced entries to fix Tally Prime import exception."""
    xml_header = """<ENVELOPE><HEADER><TALLYREQUEST>Import Data</TALLYREQUEST></HEADER><BODY><IMPORTDATA><REQUESTDESC><REPORTNAME>Vouchers</REPORTNAME></REQUESTDESC><REQUESTDATA>"""
    xml_footer = """</REQUESTDATA></IMPORTDATA></BODY></ENVELOPE>"""
    body = ""
    for _, row in df.iterrows():
        amt = row['Debit'] if row['Debit'] > 0 else row['Credit']
        if amt <= 0: continue
        vch_type = "Payment" if row['Debit'] > 0 else "Receipt"
        l1, l1_amt = (row['Final Ledger'], amt) if vch_type == "Payment" else (bank_ledger, amt)
        l2, l2_amt = (bank_ledger, -amt) if vch_type == "Payment" else (row['Final Ledger'], -amt)
        try: d = pd.to_datetime(row['Date'], dayfirst=True).strftime("%Y%m%d") #
        except: d = "20260401"
        nar = str(row['Narration']).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        body += f"""<TALLYMESSAGE><VOUCHER VCHTYPE="{vch_type}" ACTION="Create"><DATE>{d}</DATE><NARRATION>{nar}</NARRATION><ALLLEDGERENTRIES.LIST><LEDGERNAME>{l1}</LEDGERNAME><AMOUNT>{-l1_amt}</AMOUNT></ALLLEDGERENTRIES.LIST><ALLLEDGERENTRIES.LIST><LEDGERNAME>{l2}</LEDGERNAME><AMOUNT>{-l2_amt}</AMOUNT></ALLLEDGERENTRIES.LIST></VOUCHER></TALLYMESSAGE>"""
    return xml_header + body + xml_footer

# --- 4. MAIN INTERFACE ---
st.markdown('<div class="hero-container"><h1>Accounting Expert</h1><p>Turn Bank Statements into Tally Vouchers</p></div>', unsafe_allow_html=True)

col_left, col_right = st.columns([1, 1.5], gap="large")

with col_left:
    with st.container():
        st.markdown("### 🛠️ 1. Settings")
        master = st.file_uploader("Upload Tally Master", type=['html'])
        ledgers = ["Suspense A/c"]
        if master:
            soup = BeautifulSoup(master, 'html.parser')
            ledgers = sorted(list(set([t.text.strip() for t in soup.find_all('td') if t.text.strip()])))
            st.success(f"✅ {len(ledgers)} Ledgers Found")
        bank_led = st.selectbox("Select Bank Ledger", ledgers)
        part_led = st.selectbox("Select Default Party", ledgers)

with col_right:
    with st.container():
        st.markdown("### 📂 2. Upload & Convert")
        stmt = st.file_uploader("Drop Statement Here (PDF/Excel)", type=['pdf', 'xlsx'])
        if stmt:
            with st.status("🚀 Processing with AI...", expanded=False) as status:
                if stmt.name.endswith('.pdf'):
                    with pdfplumber.open(stmt) as pdf:
                        data = []
                        for page in pdf.pages:
                            table = page.extract_table()
                            if table: data.extend(table)
                    df_raw = pd.DataFrame(data)
                else:
                    df_raw = pd.read_excel(stmt)

                df_clean = smart_normalize(df_raw)
                if not df_clean.empty and 'Date' in df_clean.columns:
                    df_clean['Final Ledger'] = part_led # Auto-Trace logic can be added here
                    status.update(label="✅ Ready!", state="complete")
                    st.dataframe(df_clean[['Date', 'Narration', 'Final Ledger']].head(5), use_container_width=True)
                    if st.button("🚀 GENERATE TALLY XML"):
                        xml = generate_tally_xml(df_clean, bank_led)
                        st.download_button("⬇️ Download XML", xml, "tally_import.xml")
                else:
                    status.update(label="❌ Detection Failed", state="error")
                    st.error("Check your PDF headers (Date/Narration).")
