import streamlit as st
import pandas as pd
from PIL import Image
from bs4 import BeautifulSoup
import pdfplumber
import io
import base64

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Accounting Expert",
    page_icon="logo.png",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 2. SESSION STATE ---
if 'users_db' not in st.session_state:
    st.session_state.users_db = pd.DataFrame([
        {"Username": "admin", "Password": "123", "Role": "Admin", "Status": "Active"},
        {"Username": "uday", "Password": "123", "Role": "User", "Status": "Active"}
    ])

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.current_user = None

# --- 3. CUSTOM CSS (NAVBAR & STYLING) ---
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
        
        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif;
            background-color: #FFFFFF;
            color: #0F172A;
        }

        .stTabs {
            background-color: #0056D2;
            padding-top: 10px;
            margin-top: -6rem; 
            position: sticky;
            top: 0;
            z-index: 999;
            box-shadow: 0 4px 10px rgba(0,0,0,0.1);
        }

        .stTabs [data-baseweb="tab-list"] {
            gap: 20px;
            justify-content: flex-end;
            padding-right: 40px;
        }

        .stTabs [data-baseweb="tab"] {
            height: 60px;
            color: rgba(255, 255, 255, 0.85);
            font-weight: 500;
        }

        .stTabs [aria-selected="true"] {
            background-color: #FFFFFF !important;
            color: #0056D2 !important;
            border-radius: 50px;
            font-weight: 700;
        }

        .hero-container {
            background-color: #0056D2;
            color: white;
            padding: 40px 60px 80px 60px;
            margin: 0 -4rem 0 -4rem;
        }
        
        .hero-title {
            font-size: 3.5rem;
            font-weight: 800;
            line-height: 1.1;
            margin-bottom: 20px;
        }

        .auth-card {
            background-color: white;
            padding: 30px;
            border-radius: 12px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.15);
            color: #333;
        }

        div[data-testid="stButton"] button {
            background-color: #66E035;
            color: #0056D2;
            font-weight: 700;
            border-radius: 50px;
            width: 100%;
        }

        .footer {
            margin-top: 100px;
            padding: 30px;
            text-align: center;
            color: #64748B;
            border-top: 1px solid #eee;
        }
        
        #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- 4. LOGIC FUNCTIONS ---
def get_img_as_base64(file):
    try:
        with open(file, "rb") as f: data = f.read()
        return base64.b64encode(data).decode()
    except: return None

def get_ledger_names(html_file):
    try:
        soup = BeautifulSoup(html_file, 'html.parser')
        ledgers = []
        # Tally exports often use <td> for ledger names
        rows = soup.find_all('tr')
        for row in rows:
            cols = row.find_all('td')
            if cols:
                text = cols[0].get_text(strip=True)
                if text: ledgers.append(text)
        return sorted(list(set(ledgers))) if ledgers else ["Cash", "Bank", "Suspense A/c"]
    except: return ["Cash", "Bank", "Suspense A/c"]

def clean_currency(value):
    if pd.isna(value) or value == '': return 0.0
    val_str = str(value).replace(',', '').replace(' ', '').strip()
    try: return float(val_str)
    except: return 0.0

def extract_data_from_pdf(file, password=None):
    all_rows = []
    try:
        with pdfplumber.open(file, password=password) as pdf:
            for page in pdf.pages:
                table = page.extract_table()
                if table:
                    all_rows.extend(table)
        df = pd.DataFrame(all_rows)
        # Dynamic Header Detection
        for i, row in df.iterrows():
            row_str = row.astype(str).str.lower().values
            if any('date' in x for x in row_str) and (any('debit' in x for x in row_str) or any('withdrawal' in x for x in row_str)):
                df.columns = df.iloc[i]
                return df[i+1:].reset_index(drop=True)
        return df
    except: return None

def load_bank_file(file, password=None):
    if file.name.lower().endswith('.pdf'):
        return extract_data_from_pdf(file, password)
    return pd.read_excel(file)

def normalize_bank_data(df, bank_name):
    mappings = {
        'SBI': {'Txn Date': 'Date', 'Description': 'Narration', 'Debit': 'Debit', 'Credit': 'Credit'},
        'HDFC Bank': {'Date': 'Date', 'Narration': 'Narration', 'Withdrawal Amt.': 'Debit', 'Deposit Amt.': 'Credit'},
        'ICICI': {'Value Date': 'Date', 'Transaction Remarks': 'Narration', 'Withdrawal Amount (INR )': 'Debit', 'Deposit Amount (INR )': 'Credit'},
        # Add more mappings here as needed
    }
    if bank_name in mappings:
        df = df.rename(columns=mappings[bank_name])
    
    # Ensure standard columns exist
    for col in ['Date', 'Narration', 'Debit', 'Credit']:
        if col not in df.columns: df[col] = 0 if col in ['Debit', 'Credit'] else ""
    
    df['Debit'] = df['Debit'].apply(clean_currency)
    df['Credit'] = df['Credit'].apply(clean_currency)
    return df[['Date', 'Narration', 'Debit', 'Credit']]

def generate_tally_xml(df, bank_ledger_name, default_party_ledger):
    xml_body = ""
    for _, row in df.iterrows():
        debit, credit = row['Debit'], row['Credit']
        if debit > 0: vch_type, amount, l1, l2 = "Payment", debit, default_party_ledger, bank_ledger_name
        elif credit > 0: vch_type, amount, l1, l2 = "Receipt", credit, bank_ledger_name, default_party_ledger
        else: continue
        
        dt = pd.to_datetime(row['Date'], dayfirst=True, errors='coerce')
        date_str = dt.strftime("%Y%m%d") if pd.notnull(dt) else "20260401"
        narration = str(row['Narration']).replace("&", "&amp;").replace("<", "&lt;")
        
        xml_body += f"""<TALLYMESSAGE xmlns:UDF="TallyUDF"><VOUCHER VCHTYPE="{vch_type}" ACTION="Create"><DATE>{date_str}</DATE><NARRATION>{narration}</NARRATION><VOUCHERTYPENAME>{vch_type}</VOUCHERTYPENAME><ALLLEDGERENTRIES.LIST><LEDGERNAME>{l1}</LEDGERNAME><ISDEEMEDPOSITIVE>Yes</ISDEEMEDPOSITIVE><AMOUNT>{-amount}</AMOUNT></ALLLEDGERENTRIES.LIST><ALLLEDGERENTRIES.LIST><LEDGERNAME>{l2}</LEDGERNAME><ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE><AMOUNT>{amount}</AMOUNT></ALLLEDGERENTRIES.LIST></VOUCHER></TALLYMESSAGE>"""
    return f"<ENVELOPE><HEADER><TALLYREQUEST>Import Data</TALLYREQUEST></HEADER><BODY><IMPORTDATA><REQUESTDESC><REPORTNAME>Vouchers</REPORTNAME></REQUESTDESC><REQUESTDATA>{xml_body}</REQUESTDATA></IMPORTDATA></BODY></ENVELOPE>"

# --- 5. TABS INTERFACE ---
tabs = st.tabs(["Home", "Solutions", "Pricing", "Login", "Start Free Trial"])

with tabs[0]:
    st.markdown('<div class="hero-container">', unsafe_allow_html=True)
    if st.session_state.logged_in:
        st.markdown(f"## Welcome back, {st.session_state.current_user}!")
    else:
        col_l, col_r = st.columns([1.5, 1], gap="large")
        with col_l:
            st.markdown('<div class="hero-title">Perfecting the Science of Data Extraction</div>', unsafe_allow_html=True)
            st.markdown('<p style="font-size:1.2rem; opacity:0.9;">AI-powered tool to convert statements to Tally XML with 99% accuracy.</p>', unsafe_allow_html=True)
        with col_r:
            st.markdown('<div class="auth-card"><h3>🚀 Get Started</h3>', unsafe_allow_html=True)
            new_u = st.text_input("Username", key="reg_u")
            new_p = st.text_input("Password", type="password", key="reg_p")
            if st.button("Start Free Trial"):
                st.session_state.logged_in = True
                st.session_state.current_user = new_u
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    if st.session_state.logged_in:
        # Converter UI
        c1, c2 = st.columns([1, 1.5], gap="large")
        with c1:
            with st.container(border=True):
                st.subheader("1. Config")
                up_html = st.file_uploader("Upload Tally Master", type=['html'])
                ledgers = get_ledger_names(up_html) if up_html else ["Cash", "Bank", "Suspense A/c"]
                bank_ledger = st.selectbox("Bank Ledger", ledgers)
                party_ledger = st.selectbox("Default Party", ledgers)
        with c2:
            with st.container(border=True):
                st.subheader("2. Upload & Convert")
                bank_fmt = st.selectbox("Bank", ["SBI", "HDFC Bank", "ICICI", "Other"])
                up_file = st.file_uploader("Statement (PDF/Excel)", type=['pdf', 'xlsx'])
                if up_file:
                    df = load_bank_file(up_file)
                    if df is not None:
                        df_clean = normalize_bank_data(df, bank_fmt)
                        st.dataframe(df_clean.head(), use_container_width=True)
                        if st.button("Convert to Tally XML"):
                            xml = generate_tally_xml(df_clean, bank_ledger, party_ledger)
                            st.download_button("Download XML", xml, "tally.xml")

# Footer
st.markdown(f'<div class="footer"><p>Sponsored By <b>Uday Mondal</b> | Powered by <b>Debasish Biswas</b></p></div>', unsafe_allow_html=True)
