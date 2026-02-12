import streamlit as st
import pandas as pd
from PIL import Image
from bs4 import BeautifulSoup
import pdfplumber
import io
import base64
import re

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Accounting Expert | AI Bank to Tally",
    page_icon="logo.png",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 2. FUTURISTIC TALLY THEME CSS ---
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
        html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #F8FAFC; color: #0F172A; }
        .hero-container {
            text-align: center; padding: 50px 20px;
            background: linear-gradient(135deg, #065F46 0%, #1E40AF 100%);
            color: white; margin: -6rem -4rem 30px -4rem;
            box-shadow: 0 10px 30px -10px rgba(6, 95, 70, 0.5);
            position: relative; overflow: hidden;
        }
        .hero-container::before {
            content: ""; position: absolute; top: 0; left: 0; right: 0; bottom: 0;
            background-image: linear-gradient(rgba(255, 255, 255, 0.1) 1px, transparent 1px), 
                              linear-gradient(90deg, rgba(255, 255, 255, 0.1) 1px, transparent 1px);
            background-size: 30px 30px; pointer-events: none;
        }
        .hero-title { font-size: 3.5rem; font-weight: 800; margin-top: 10px; text-shadow: 0 4px 10px rgba(0,0,0,0.3); }
        .hero-subtitle { font-size: 1.2rem; color: #E2E8F0; font-weight: 300; opacity: 0.9; }
        .stContainer { background-color: white; padding: 30px; border-radius: 16px; box-shadow: 0 4px 20px -5px rgba(0, 0, 0, 0.05); border: 1px solid #E2E8F0; }
        h3 { font-size: 1.2rem !important; font-weight: 700 !important; color: #1e293b !important; border-left: 5px solid #10B981; padding-left: 12px; }
        .stButton>button { width: 100%; background: linear-gradient(90deg, #10B981 0%, #3B82F6 100%); color: white; border-radius: 8px; height: 55px; font-weight: 600; border: none; transition: all 0.3s ease; }
        .stButton>button:hover { transform: translateY(-2px); box-shadow: 0 8px 25px rgba(16, 185, 129, 0.4); }
        .footer { margin-top: 60px; padding: 40px; text-align: center; color: #64748B; font-size: 0.9rem; border-top: 1px solid #E2E8F0; background-color: white; margin-bottom: -60px; }
        .brand-link { color: #059669; text-decoration: none; font-weight: 700; }
        #MainMenu, footer, header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- 3. HELPER & TRACING FUNCTIONS ---

def get_img_as_base64(file):
    try:
        with open(file, "rb") as f: return base64.b64encode(f.read()).decode()
    except: return None

def get_ledger_names(html_file):
    try:
        soup = BeautifulSoup(html_file, 'html.parser')
        ledgers = []
        for row in soup.find_all('tr'):
            cols = row.find_all('td')
            if cols:
                text = cols[0].get_text(strip=True)
                if text: ledgers.append(text)
        if not ledgers:
            lines = [line.strip() for line in soup.get_text(separator='\n').split('\n') if line.strip()]
            ledgers = list(set(lines))
        return sorted(ledgers)
    except: return []

def trace_ledger(narration, master_ledgers):
    """Identity-First Tracing using Reverse-Length Matching and Word Boundaries."""
    if not narration or not master_ledgers: return None
    sorted_ledgers = sorted(master_ledgers, key=len, reverse=True) #
    for ledger in sorted_ledgers:
        if len(ledger) < 3: continue 
        pattern = r'\b' + re.escape(ledger) + r'\b' #
        if re.search(pattern, str(narration), re.IGNORECASE):
            return ledger
    return None

def clean_currency(value):
    if pd.isna(value) or value == '': return 0.0
    try: return float(str(value).replace(',', '').strip())
    except: return 0.0

def extract_data_from_pdf(file, password=None):
    all_rows = []
    try:
        with pdfplumber.open(file, password=password) as pdf:
            for page in pdf.pages:
                table = page.extract_table()
                if table:
                    for row in table:
                        all_rows.append([str(cell).replace('\n', ' ').strip() if cell else '' for cell in row])
        if not all_rows: return None
        df = pd.DataFrame(all_rows)
        for i, row in df.iterrows():
            row_str = row.astype(str).str.lower().values
            if any('date' in x for x in row_str) and (any('balance' in x for x in row_str) or any('debit' in x for x in row_str)):
                df.columns = df.iloc[i]; df = df[i + 1:]; break
        return df
    except: return None

def normalize_bank_data(df, bank_name):
    df.columns = df.columns.astype(str).str.replace('\n', ' ').str.strip()
    target = ['Date', 'Narration', 'Debit', 'Credit']
    mappings = {
        'SBI': {'Txn Date': 'Date', 'Description': 'Narration'},
        'PNB': {'Transaction Date': 'Date', 'Narration': 'Narration'},
        'ICICI': {'Value Date': 'Date', 'Transaction Remarks': 'Narration', 'Withdrawal Amount (INR )': 'Debit', 'Deposit Amount (INR )': 'Credit'},
        'HDFC Bank': {'Date': 'Date', 'Narration': 'Narration', 'Withdrawal Amt.': 'Debit', 'Deposit Amt.': 'Credit'},
        'Axis Bank': {'Tran Date': 'Date', 'Particulars': 'Narration'}
    }
    mapping = mappings.get(bank_name, {})
    df = df.rename(columns=mapping)
    for col in target:
        if col not in df.columns: df[col] = 0 if col in ['Debit', 'Credit'] else ""
    df['Debit'] = df['Debit'].apply(clean_currency)
    df['Credit'] = df['Credit'].apply(clean_currency)
    return df[target]

def generate_tally_xml(df, bank_ledger_name):
    xml_header = """<ENVELOPE><HEADER><TALLYREQUEST>Import Data</TALLYREQUEST></HEADER><BODY><IMPORTDATA><REQUESTDESC><REPORTNAME>Vouchers</REPORTNAME></REQUESTDESC><REQUESTDATA>"""
    xml_footer = """</REQUESTDATA></IMPORTDATA></BODY></ENVELOPE>"""
    xml_body = ""
    for _, row in df.iterrows():
        amt = row['Debit'] if row['Debit'] > 0 else row['Credit']
        if amt <= 0: continue
        vch_type = "Payment" if row['Debit'] > 0 else "Receipt"
        led1, led1_amt = (row['Final Ledger'], -amt) if vch_type == "Payment" else (bank_ledger_name, -amt)
        led2, led2_amt = (bank_ledger_name, amt) if vch_type == "Payment" else (row['Final Ledger'], amt)
        
        try: date_str = pd.to_datetime(row['Date'], dayfirst=True).strftime("%Y%m%d")
        except: date_str = "20260401"
        nar = str(row['Narration']).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

        xml_body += f"""<TALLYMESSAGE xmlns:UDF="TallyUDF"><VOUCHER VCHTYPE="{vch_type}" ACTION="Create"><DATE>{date_str}</DATE><NARRATION>{nar}</NARRATION><VOUCHERTYPENAME>{vch_type}</VOUCHERTYPENAME><ALLLEDGERENTRIES.LIST><LEDGERNAME>{led1}</LEDGERNAME><ISDEEMEDPOSITIVE>Yes</ISDEEMEDPOSITIVE><AMOUNT>{led1_amt}</AMOUNT></ALLLEDGERENTRIES.LIST><ALLLEDGERENTRIES.LIST><LEDGERNAME>{led2}</LEDGERNAME><ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE><AMOUNT>{led2_amt}</AMOUNT></ALLLEDGERENTRIES.LIST></VOUCHER></TALLYMESSAGE>"""
    return xml_header + xml_body + xml_footer

# --- 4. UI RENDER ---
hero_logo_b64 = get_img_as_base64("logo.png")
hero_logo_html = f'<img src="data:image/png;base64,{hero_logo_b64}" width="120" style="margin-bottom: 20px;">' if hero_logo_b64 else ""
st.markdown(f'<div class="hero-container">{hero_logo_html}<div class="hero-title">Accounting Expert</div><div class="hero-subtitle">Auto-Trace Bank Statements into Tally Vouchers.</div></div>', unsafe_allow_html=True)

col_left, col_right = st.columns([1, 1.5], gap="large")

with col_left:
    with st.container():
        st.markdown("### 🛠️ 1. Settings")
        uploaded_html = st.file_uploader("Upload Tally Master", type=['html', 'htm'])
        ledger_list = ["Suspense A/c", "Cash", "Bank"]
        if uploaded_html:
            extracted = get_ledger_names(uploaded_html)
            if extracted: ledger_list = extracted; st.success(f"✅ {len(ledger_list)} Ledgers Synced")
        bank_ledger = st.selectbox("Select Bank Ledger", ledger_list)
        party_ledger = st.selectbox("Select Default Party", ledger_list)

with col_right:
    with st.container():
        st.markdown("### 📂 2. Upload & Trace")
        c1, c2 = st.columns(2)
        bank_choice = c1.selectbox("Format", ["SBI", "PNB", "ICICI", "Axis Bank", "HDFC Bank", "Other"])
        pdf_password = c2.text_input("Password", type="password")
        uploaded_file = st.file_uploader("Upload Statement", type=['xlsx', 'xls', 'pdf'])
        
        if uploaded_file:
            df_raw = extract_data_from_pdf(uploaded_file, pdf_password) if uploaded_file.name.endswith('.pdf') else pd.read_excel(uploaded_file)
            if df_raw is not None:
                df_clean = normalize_bank_data(df_raw, bank_choice)
                # Auto-Trace Application
                df_clean['Suggested'] = df_clean['Narration'].apply(lambda x: trace_ledger(x, ledger_list))
                df_clean['Final Ledger'] = df_clean['Suggested'].fillna(party_ledger)
                df_clean['Status'] = df_clean.apply(lambda x: "✅ Matched" if pd.notna(x['Suggested']) else ("⚠️ UPI Alert" if "UPI" in str(x['Narration']).upper() else "ℹ️ Default"), axis=1) #
                
                st.dataframe(df_clean[['Date', 'Narration', 'Final Ledger', 'Status']].head(10), use_container_width=True)
                if st.button("🚀 Convert to Tally XML"):
                    xml_data = generate_tally_xml(df_clean, bank_ledger)
                    st.balloons()
                    st.download_button("⬇️ Download XML", xml_data, "tally_import.xml")

footer_logo_b64 = get_img_as_base64("logo 1.png")
footer_img = f'<img src="data:image/png;base64,{footer_logo_b64}" width="25" style="vertical-align: middle;">' if footer_logo_b64 else ""
st.markdown(f'<div class="footer"><p>Sponsored By {footer_img} <b>Uday Mondal</b> | Consultant Advocate</p><p>Created by <b>Debasish Biswas</b></p></div>', unsafe_allow_html=True)
