import streamlit as st
import pandas as pd
from bs4 import BeautifulSoup
import pdfplumber
import re
import time

# --- 1. PAGE CONFIGS ---
st.set_page_config(page_title="Accounting Expert AI", layout="wide", page_icon="🚀")

# --- 2. FUTURISTIC ANIMATION CSS ---
st.markdown("""
    <style>
        /* Pulse Animation for Processing */
        @keyframes pulse {
            0% { opacity: 0.5; }
            50% { opacity: 1; }
            100% { opacity: 0.5; }
        }
        .processing-text {
            color: #10B981;
            font-weight: 700;
            animation: pulse 1.5s infinite;
            text-align: center;
            font-size: 1.2rem;
        }
        .stProgress > div > div > div > div {
            background-image: linear-gradient(to right, #10B981 , #3B82F6);
        }
        #MainMenu, footer, header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- 3. CORE LOGIC ---

def clean_currency(value):
    if pd.isna(value) or value == '': return 0.0
    val = re.sub(r'[^\d.]', '', str(value))
    try: return float(val)
    except: return 0.0

def trace_ledger(narration, master_ledgers):
    if not narration or not master_ledgers: return None
    sorted_masters = sorted([str(m) for m in master_ledgers], key=len, reverse=True)
    for ledger in sorted_masters:
        if len(ledger) < 3: continue
        pattern = r'\b' + re.escape(ledger) + r'\b'
        if re.search(pattern, str(narration), re.IGNORECASE):
            return ledger
    return None

def smart_normalize(df):
    """Refined to prevent AttributeError and handle messy PDF tables."""
    if df is None or df.empty: return pd.DataFrame()
    
    # Filter out completely empty rows/cols
    df = df.dropna(how='all').reset_index(drop=True)
    
    header_idx = None
    for i, row in df.iterrows():
        # Safeguard: ensure the row has string content to join
        row_str = " ".join([str(item).lower() for item in row.values if item is not None])
        if 'date' in row_str and ('narration' in row_str or 'particular' in row_str or 'description' in row_str):
            header_idx = i
            break
    
    if header_idx is not None:
        df.columns = df.iloc[header_idx]
        df = df[header_idx + 1:].reset_index(drop=True)
    
    df.columns = df.columns.astype(str).str.strip().str.lower()

    new_df = pd.DataFrame()
    col_map = {
        'Date': ['date', 'txn', 'value', 'tran'],
        'Narration': ['narration', 'description', 'particulars', 'remarks', 'details'],
        'Debit': ['debit', 'withdrawal', 'out', 'dr'],
        'Credit': ['credit', 'deposit', 'in', 'cr']
    }

    for target, aliases in col_map.items():
        found_col = next((c for c in df.columns if any(a in c for a in aliases)), None)
        if found_col:
            new_df[target] = df[found_col]
        else:
            new_df[target] = 0.0 if target in ['Debit', 'Credit'] else ""

    new_df['Debit'] = new_df['Debit'].apply(clean_currency)
    new_df['Credit'] = new_df['Credit'].apply(clean_currency)
    return new_df.dropna(subset=['Date'])

def generate_tally_xml(df, bank_ledger):
    xml_header = """<ENVELOPE><HEADER><TALLYREQUEST>Import Data</TALLYREQUEST></HEADER><BODY><IMPORTDATA><REQUESTDESC><REPORTNAME>Vouchers</REPORTNAME></REQUESTDESC><REQUESTDATA>"""
    xml_footer = """</REQUESTDATA></IMPORTDATA></BODY></ENVELOPE>"""
    body = ""
    for _, row in df.iterrows():
        amt = row['Debit'] if row['Debit'] > 0 else row['Credit']
        if amt <= 0: continue
        vch_type = "Payment" if row['Debit'] > 0 else "Receipt"
        
        # Tally logic: Credits are stored as negative numbers internally
        l1, l1_amt = (row['Final Ledger'], amt) if vch_type == "Payment" else (bank_ledger, amt)
        l2, l2_amt = (bank_ledger, -amt) if vch_type == "Payment" else (row['Final Ledger'], -amt)

        try: d = pd.to_datetime(row['Date'], dayfirst=True).strftime("%Y%m%d")
        except: d = "20260401" #
        
        nar = str(row['Narration']).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        
        body += f"""<TALLYMESSAGE xmlns:UDF="TallyUDF"><VOUCHER VCHTYPE="{vch_type}" ACTION="Create"><DATE>{d}</DATE><NARRATION>{nar}</NARRATION><VOUCHERTYPENAME>{vch_type}</VOUCHERTYPENAME><ALLLEDGERENTRIES.LIST><LEDGERNAME>{l1}</LEDGERNAME><ISDEEMEDPOSITIVE>{"Yes" if l1_amt > 0 else "No"}</ISDEEMEDPOSITIVE><AMOUNT>{-l1_amt}</AMOUNT></ALLLEDGERENTRIES.LIST><ALLLEDGERENTRIES.LIST><LEDGERNAME>{l2}</LEDGERNAME><ISDEEMEDPOSITIVE>{"Yes" if l2_amt > 0 else "No"}</ISDEEMEDPOSITIVE><AMOUNT>{-l2_amt}</AMOUNT></ALLLEDGERENTRIES.LIST></VOUCHER></TALLYMESSAGE>"""
    return xml_header + body + xml_footer

# --- 4. UI RENDER ---
st.title("Accounting Expert | AI Engine")

col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("1. Setup")
    master = st.file_uploader("Upload Tally Master", type=['html'])
    ledgers = ["Suspense A/c"]
    if master:
        soup = BeautifulSoup(master, 'html.parser')
        ledgers = sorted(list(set([t.text.strip() for t in soup.find_all('td') if t.text.strip()])))
        st.success(f"Synced {len(ledgers)} Ledgers")
    
    bank_led = st.selectbox("Bank Ledger", ledgers)
    part_led = st.selectbox("Default Party", ledgers)

with col2:
    st.subheader("2. Analysis")
    stmt = st.file_uploader("Upload Statement", type=['pdf', 'xlsx'])
    
    if stmt:
        # --- FUTURISTIC PROCESSING ANIMATION ---
        with st.status("🚀 AI Engine Initializing...", expanded=True) as status:
            st.write("🔍 Scanning Document Structure...")
            time.sleep(0.8)
            
            if stmt.name.endswith('.pdf'):
                with pdfplumber.open(stmt) as pdf:
                    data = []
                    for p in pdf.pages: data.extend(p.extract_table() or [])
                df_raw = pd.DataFrame(data)
            else:
                df_raw = pd.read_excel(stmt)

            st.write("🧠 Mapping Ledgers with Auto-Trace...")
            time.sleep(0.6)
            
            if not df_raw.empty:
                df_clean = smart_normalize(df_raw)
                if not df_clean.empty:
                    df_clean['Final Ledger'] = df_clean['Narration'].apply(lambda x: trace_ledger(x, ledgers) or part_led)
                    status.update(label="✅ Analysis Complete!", state="complete", expanded=False)
                else:
                    status.update(label="❌ Header Detection Failed", state="error")
                    st.error("Check your PDF layout—I couldn't find 'Date' or 'Narration' columns.")
            else:
                status.update(label="❌ Empty File", state="error")

        if 'df_clean' in locals() and not df_clean.empty:
            st.markdown('<p class="processing-text">Previewing Traced Transactions</p>', unsafe_allow_html=True)
            st.dataframe(df_clean[['Date', 'Narration', 'Final Ledger', 'Debit', 'Credit']], use_container_width=True)
            
            if st.button("✨ Finalize & Generate XML"):
                progress_bar = st.progress(0)
                for percent_complete in range(100):
                    time.sleep(0.01)
                    progress_bar.progress(percent_complete + 1)
                
                xml = generate_tally_xml(df_clean, bank_led)
                st.balloons()
                st.download_button("⬇️ Download Tally XML", xml, "tally_import.xml")
