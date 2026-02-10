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

# --- 3. CUSTOM CSS ---
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
        
        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif;
            background-color: #FFFFFF;
            color: #0F172A;
        }

        /* --- NAVIGATION TABS --- */
        .stTabs {
            background-color: #0056D2;
            padding-top: 10px;
            padding-bottom: 0px;
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
            white-space: pre-wrap;
            background-color: transparent;
            border: none;
            color: rgba(255, 255, 255, 0.85);
            font-weight: 500;
            font-size: 1rem;
            padding: 0 15px;
        }

        .stTabs [aria-selected="true"] {
            background-color: #FFFFFF !important;
            color: #0056D2 !important;
            border-radius: 50px;
            font-weight: 700;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
        }

        /* --- HERO SECTION --- */
        .hero-container {
            background-color: transparent; 
            color: #0F172A;
            padding: 40px 60px 80px 60px;
            margin: 0 -4rem 0 -4rem;
        }
        
        .hero-title {
            font-size: 3.5rem;
            font-weight: 800;
            line-height: 1.1;
            margin-bottom: 20px;
            color: #0F172A !important;
        }
        
        .hero-subtitle {
            font-size: 1.2rem;
            opacity: 0.9;
            margin-bottom: 30px;
            line-height: 1.6;
            color: #475569 !important;
        }

        /* --- FORM CARDS --- */
        .auth-card {
            background-color: white;
            padding: 30px;
            border-radius: 12px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.15);
            color: #333;
            border: 1px solid #E2E8F0;
        }

        /* --- BUTTONS --- */
        div[data-testid="stButton"] button {
            background-color: #66E035;
            color: #0056D2;
            font-weight: 700;
            border-radius: 50px;
            border: none;
            width: 100%;
            padding: 12px;
        }

        /* --- PINNED FOOTER --- */
        .footer {
            position: fixed;
            left: 0;
            bottom: 0;
            width: 100%;
            background-color: white;
            color: #64748B;
            text-align: center;
            padding: 15px 0;
            border-top: 1px solid #eee;
            z-index: 1000;
            box-shadow: 0 -2px 10px rgba(0,0,0,0.05);
        }

        /* Padding for Main Content to clear pinned footer */
        .main .block-container {
            padding-bottom: 120px;
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
        rows = soup.find_all('tr')
        for row in rows:
            cols = row.find_all('td')
            if cols:
                text = cols[0].get_text(strip=True)
                if text: ledgers.append(text)
        return sorted(list(set(ledgers)))
    except: return []

def clean_currency(value):
    if pd.isna(value) or value == '': return 0.0
    val_str = str(value).replace(',', '').strip()
    try: return float(val_str)
    except: return 0.0

def load_bank_file(file, password=None):
    if file.name.lower().endswith('.pdf'):
        all_rows = []
        with pdfplumber.open(file, password=password) as pdf:
            for page in pdf.pages:
                table = page.extract_table()
                if table:
                    for row in table:
                        all_rows.append([str(c).replace('\n', ' ').strip() if c else '' for c in row])
        df = pd.DataFrame(all_rows)
        for i, row in df.iterrows():
            if any('date' in str(x).lower() for x in row):
                df.columns = df.iloc[i]
                return df[i+1:]
        return df
    return pd.read_excel(file)

def normalize_bank_data(df, bank_name):
    mappings = {
        'SBI': {'Txn Date': 'Date', 'Description': 'Narration', 'Debit': 'Debit', 'Credit': 'Credit'},
        'HDFC Bank': {'Date': 'Date', 'Narration': 'Narration', 'Withdrawal Amt.': 'Debit', 'Deposit Amt.': 'Credit'},
        'ICICI': {'Value Date': 'Date', 'Transaction Remarks': 'Narration', 'Withdrawal Amount (INR )': 'Debit', 'Deposit Amount (INR )': 'Credit'}
    }
    if bank_name in mappings: df = df.rename(columns=mappings[bank_name])
    for col in ['Date', 'Narration', 'Debit', 'Credit']:
        if col not in df.columns: df[col] = 0 if col in ['Debit', 'Credit'] else ""
    df['Debit'] = df['Debit'].apply(clean_currency)
    df['Credit'] = df['Credit'].apply(clean_currency)
    return df[['Date', 'Narration', 'Debit', 'Credit']]

def generate_tally_xml(df, bank_ledger_name, default_party_ledger):
    xml_body = ""
    for _, row in df.iterrows():
        d, c = row['Debit'], row['Credit']
        if d > 0: v, a, l1, l2 = "Payment", d, default_party_ledger, bank_ledger_name
        elif c > 0: v, a, l1, l2 = "Receipt", c, bank_ledger_name, default_party_ledger
        else: continue
        try: dt = pd.to_datetime(row['Date'], dayfirst=True).strftime("%Y%m%d")
        except: dt = "20240401"
        xml_body += f"""<TALLYMESSAGE xmlns:UDF="TallyUDF"><VOUCHER VCHTYPE="{v}" ACTION="Create"><DATE>{dt}</DATE><NARRATION>{row['Narration']}</NARRATION><VOUCHERTYPENAME>{v}</VOUCHERTYPENAME><ALLLEDGERENTRIES.LIST><LEDGERNAME>{l1}</LEDGERNAME><ISDEEMEDPOSITIVE>Yes</ISDEEMEDPOSITIVE><AMOUNT>{-a}</AMOUNT></ALLLEDGERENTRIES.LIST><ALLLEDGERENTRIES.LIST><LEDGERNAME>{l2}</LEDGERNAME><ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE><AMOUNT>{a}</AMOUNT></ALLLEDGERENTRIES.LIST></VOUCHER></TALLYMESSAGE>"""
    return f"<ENVELOPE><BODY><IMPORTDATA><REQUESTDATA>{xml_body}</REQUESTDATA></IMPORTDATA></BODY></ENVELOPE>"

# --- 5. MAIN RENDER ---
tabs = st.tabs(["Home", "Solutions", "Pricing", "Login", "Start Free Trial"])

with tabs[0]:
    st.markdown('<div class="hero-container">', unsafe_allow_html=True)
    if st.session_state.logged_in:
        st.markdown(f"## Welcome back, {st.session_state.current_user}!")
        st.write("Upload your files below to begin conversion.")
    else:
        col_l, col_r = st.columns([1.5, 1], gap="large")
        with col_l:
            st.markdown('<div class="hero-title">Perfecting the Science of Data Extraction</div>', unsafe_allow_html=True)
            st.markdown('<div class="hero-subtitle">AI-powered tool to convert bank statements and financial documents into Tally XML with 99% accuracy.</div>', unsafe_allow_html=True)
            try: 
                logo_b64 = get_img_as_base64("logo.png")
                if logo_b64: st.markdown(f'<img src="data:image/png;base64,{logo_b64}" width="150" style="margin-top:20px;">', unsafe_allow_html=True)
            except: pass
        with col_r:
            st.markdown('<div class="auth-card"><h3>🚀 Get Started</h3>', unsafe_allow_html=True)
            u = st.text_input("Username", key="reg_u", placeholder="Create Username")
            p = st.text_input("Password", type="password", key="reg_p", placeholder="Create Password")
            if st.button("Start Free Trial Now"):
                st.session_state.logged_in = True
                st.session_state.current_user = u
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    if st.session_state.logged_in:
        # Converter UI logic here
        st.markdown("<br>", unsafe_allow_html=True)
        c1, c2 = st.columns([1, 1.5], gap="large")
        with c1:
            with st.container(border=True):
                st.markdown("### 🛠️ 1. Configuration")
                up_html = st.file_uploader("Upload Tally Master", type=['html'])
                ledgers = get_ledger_names(up_html) if up_html else ["Cash", "Bank", "Suspense A/c"]
                bank_ledg = st.selectbox("Bank Ledger", ledgers)
                part_ledg = st.selectbox("Party Ledger", ledgers)
        with c2:
            with st.container(border=True):
                st.markdown("### 📂 2. Process")
                bank_fmt = st.selectbox("Format", ["SBI", "HDFC Bank", "ICICI", "Other"])
                up_file = st.file_uploader("Upload Statement", type=['xlsx', 'pdf'])
                if up_file:
                    df = load_bank_file(up_file)
                    if df is not None:
                        df_c = normalize_bank_data(df, bank_fmt)
                        st.dataframe(df_c.head(3), use_container_width=True)
                        if st.button("🚀 Convert to Tally XML"):
                            xml = generate_tally_xml(df_c, bank_ledg, part_ledg)
                            st.download_button("Download XML", xml, "import.xml")

with tabs[1]:
    st.markdown("### 🌟 Our Solutions")
    st.write("1. **Bank Statement to Tally**: Seamlessly import any bank PDF/Excel.")
    st.write("2. **Master Ledger Sync**: Auto-detect ledgers from your Tally HTML export.")

with tabs[2]:
    st.markdown("### 💰 Simple Pricing")
    st.write("- **Free Trial**: 10 conversions (No credit card).")
    st.write("- **Pro Plan**: ₹499/month for unlimited conversions.")

with tabs[3]:
    st.markdown("### 🔐 User Login")
    u_login = st.text_input("Username", key="login_u")
    p_login = st.text_input("Password", type="password", key="login_p")
    if st.button("Login"):
        st.session_state.logged_in = True
        st.session_state.current_user = u_login
        st.rerun()

with tabs[4]:
    st.info("Registration is available on the Home page.")

# --- 6. PINNED GLOBAL FOOTER ---
try: 
    uday_logo_b64 = get_img_as_base64("logo 1.png")
except: 
    uday_logo_b64 = None

uday_logo_html = f'<img src="data:image/png;base64,{uday_logo_b64}" width="20" style="vertical-align: middle; margin-right: 5px;">' if uday_logo_b64 else ""

st.markdown(f"""
    <div class="footer">
        <p style="margin-bottom: 5px;">
            Sponsored By {uday_logo_html} 
            <span style="color:#0044CC; font-weight:700">Uday Mondal</span> | Consultant Advocate
        </p>
        <p style="font-size: 12px; margin: 0;">
            Powered & Created by <span style="color:#0044CC; font-weight:700">Debasish Biswas</span>
        </p>
    </div>
""", unsafe_allow_html=True)
