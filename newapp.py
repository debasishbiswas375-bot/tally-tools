import streamlit as st
import pandas as pd
from PIL import Image
from bs4 import BeautifulSoup
import pdfplumber
import io
import base64
import time

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Accounting Expert | AI Bank to Tally",
    page_icon="logo.png",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 2. SESSION STATE (DATABASE & LOGIN) ---
# This acts as your database for now.
if 'users_db' not in st.session_state:
    st.session_state.users_db = pd.DataFrame([
        {"Username": "admin", "Password": "123", "Role": "Admin", "Status": "Active"},
        {"Username": "uday", "Password": "123", "Role": "User", "Status": "Active"}
    ])

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.current_user = None

# --- 3. CUSTOM CSS (CAELUM STYLE + TABS) ---
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
        
        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif;
            background-color: #F8FAFC; 
            color: #0F172A;
        }

        /* --- STYLING STREAMLIT TABS TO LOOK LIKE NAVBAR --- */
        .stTabs [data-baseweb="tab-list"] {
            gap: 10px;
            background-color: #0044CC; /* Caelum Blue */
            padding: 10px 20px;
            border-radius: 0px 0px 10px 10px;
            margin-top: -6rem; /* Pull up to top */
            position: sticky;
            top: 0;
            z-index: 100;
        }

        .stTabs [data-baseweb="tab"] {
            height: 50px;
            white-space: pre-wrap;
            background-color: transparent;
            border-radius: 4px;
            color: rgba(255, 255, 255, 0.7);
            font-weight: 600;
            font-size: 1rem;
            border: none;
        }

        .stTabs [aria-selected="true"] {
            background-color: rgba(255, 255, 255, 0.2) !important;
            color: white !important;
            border-bottom: 3px solid #4ADE80; /* Green highlight */
        }

        /* --- HERO SECTION --- */
        .hero-section {
            background-color: #0044CC;
            color: white;
            padding: 40px 80px 80px 80px;
            margin: 0 -4rem 30px -4rem;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        
        .hero-title { font-size: 3rem; font-weight: 800; line-height: 1.1; margin-bottom: 20px; }
        .hero-subtitle { font-size: 1.1rem; opacity: 0.9; margin-bottom: 30px; }
        
        /* CARD STYLING */
        .stContainer {
            background-color: white;
            padding: 30px;
            border-radius: 12px;
            box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
            border: 1px solid #E2E8F0;
        }
        
        /* Buttons */
        div[data-testid="stButton"] button {
             background-color: #0044CC; 
             color: white; 
             font-weight: 600;
             border-radius: 8px;
        }
        
        /* Footer */
        .footer {
            margin-top: 60px; padding: 40px; text-align: center; 
            color: #64748B; border-top: 1px solid #E2E8F0;
            background-color: white; margin-bottom: -60px;
        }
        
        #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- 4. HELPER FUNCTIONS ---
def get_img_as_base64(file):
    try:
        with open(file, "rb") as f: data = f.read()
        return base64.b64encode(data).decode()
    except: return None

def clean_currency(value):
    if pd.isna(value) or value == '': return 0.0
    val_str = str(value).replace(',', '').strip()
    try: return float(val_str)
    except: return 0.0

def load_bank_file(file, password=None):
    if file.name.lower().endswith('.pdf'):
        # PDF Logic embedded directly here for brevity
        all_rows = []
        try:
            with pdfplumber.open(file, password=password) as pdf:
                for page in pdf.pages:
                    table = page.extract_table()
                    if table:
                        for row in table:
                            cleaned = [str(cell).replace('\n', ' ').strip() if cell else '' for cell in row]
                            if any(cleaned): all_rows.append(cleaned)
            if not all_rows: return None
            df = pd.DataFrame(all_rows)
            # Simple Header Search
            header_idx = 0
            for i, row in df.iterrows():
                row_str = row.astype(str).str.lower().values
                if any('date' in x for x in row_str):
                    header_idx = i; break
            df.columns = df.iloc[header_idx]; df = df[header_idx + 1:]; return df
        except: return None
    else:
        try: return pd.read_excel(file)
        except: return None

def normalize_bank_data(df, bank_name):
    df.columns = df.columns.astype(str).str.replace('\n', ' ').str.strip()
    target_columns = ['Date', 'Narration', 'Debit', 'Credit']
    mappings = {
        'SBI': {'Txn Date': 'Date', 'Description': 'Narration', 'Debit': 'Debit', 'Credit': 'Credit'},
        'PNB': {'Transaction Date': 'Date', 'Narration': 'Narration', 'Debit Amount': 'Debit', 'Credit Amount': 'Credit'},
        'ICICI': {'Value Date': 'Date', 'Transaction Remarks': 'Narration', 'Withdrawal Amount (INR )': 'Debit', 'Deposit Amount (INR )': 'Credit'},
        'HDFC Bank': {'Date': 'Date', 'Narration': 'Narration', 'Withdrawal Amt.': 'Debit', 'Deposit Amt.': 'Credit'},
        'Axis Bank': {'Tran Date': 'Date', 'Particulars': 'Narration', 'Debit': 'Debit', 'Credit': 'Credit'},
    }
    # Basic mapping logic
    if bank_name in mappings:
        df = df.rename(columns=mappings[bank_name])
    
    # Ensure columns exist
    for col in target_columns:
        if col not in df.columns: df[col] = 0 if col in ['Debit', 'Credit'] else ""
            
    df['Debit'] = df['Debit'].apply(clean_currency)
    df['Credit'] = df['Credit'].apply(clean_currency)
    df['Narration'] = df['Narration'].fillna('')
    return df[target_columns]

def generate_tally_xml(df, bank_ledger_name, default_party_ledger):
    xml_body = ""
    for index, row in df.iterrows():
        debit, credit = row['Debit'], row['Credit']
        if debit > 0: vch_type, amt, l1, l2 = "Payment", debit, default_party_ledger, bank_ledger_name
        elif credit > 0: vch_type, amt, l1, l2 = "Receipt", credit, bank_ledger_name, default_party_ledger
        else: continue
        
        try: date_str = pd.to_datetime(row['Date'], dayfirst=True).strftime("%Y%m%d")
        except: date_str = "20240401"
        narration = str(row['Narration']).replace("&", "&amp;").replace("<", "&lt;")

        xml_body += f"""<TALLYMESSAGE xmlns:UDF="TallyUDF"><VOUCHER VCHTYPE="{vch_type}" ACTION="Create" OBJVIEW="Accounting Voucher View"><DATE>{date_str}</DATE><NARRATION>{narration}</NARRATION><VOUCHERTYPENAME>{vch_type}</VOUCHERTYPENAME><ALLLEDGERENTRIES.LIST><LEDGERNAME>{l1}</LEDGERNAME><ISDEEMEDPOSITIVE>Yes</ISDEEMEDPOSITIVE><AMOUNT>{-amt}</AMOUNT></ALLLEDGERENTRIES.LIST><ALLLEDGERENTRIES.LIST><LEDGERNAME>{l2}</LEDGERNAME><ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE><AMOUNT>{amt}</AMOUNT></ALLLEDGERENTRIES.LIST></VOUCHER></TALLYMESSAGE>"""
    return f"<ENVELOPE><HEADER><TALLYREQUEST>Import Data</TALLYREQUEST></HEADER><BODY><IMPORTDATA><REQUESTDESC><REPORTNAME>Vouchers</REPORTNAME></REQUESTDESC><REQUESTDATA>{xml_body}</REQUESTDATA></IMPORTDATA></BODY></ENVELOPE>"

# --- 5. MAIN NAVIGATION (Active Tabs) ---
# This creates the functional Top Bar
tabs = st.tabs(["🏠 Home", "🛠️ User Management", "💎 Pricing"])

# --- TAB 1: HOME (THE CONVERTER) ---
with tabs[0]:
    # Hero Section
    try: hero_logo_b64 = get_img_as_base64("logo.png")
    except: hero_logo_b64 = None
    hero_img_html = f'<img src="data:image/png;base64,{hero_logo_b64}" style="max-width: 100%; animation: float 6s ease-in-out infinite;">' if hero_logo_b64 else ""

    st.markdown(f"""
        <div class="hero-section">
            <div class="hero-content">
                <div class="hero-title">Accounting Expert AI</div>
                <div class="hero-subtitle">Convert PDF & Excel Bank Statements to Tally XML instantly. <br>Secure, Fast, and 99% Accurate.</div>
            </div>
            <div style="width: 300px;">{hero_img_html}</div>
        </div>
    """, unsafe_allow_html=True)

    # Converter UI
    col_left, col_right = st.columns([1, 1.5], gap="large")
    
    with col_left:
        with st.container(border=True):
            st.markdown("### 1. Settings")
            bank_ledger = st.text_input("Bank Ledger Name", value="Bank")
            party_ledger = st.text_input("Default Party/Suspense", value="Suspense A/c")

    with col_right:
        with st.container(border=True):
            st.markdown("### 2. Upload & Convert")
            c1, c2 = st.columns([1.5, 1])
            with c1: bank_choice = st.selectbox("Bank Format", ["SBI", "PNB", "ICICI", "Axis Bank", "HDFC Bank", "Other"])
            with c2: pdf_pass = st.text_input("PDF Password", type="password")

            uploaded_file = st.file_uploader("Upload Statement", type=['xlsx', 'xls', 'pdf'])
            
            if uploaded_file:
                with st.spinner("Processing..."):
                    df_raw = load_bank_file(uploaded_file, pdf_pass)
                
                if df_raw is not None:
                    df_clean = normalize_bank_data(df_raw, bank_choice)
                    st.dataframe(df_clean.head(3), use_container_width=True, hide_index=True)
                    if st.button("🚀 Convert to XML", type="primary"):
                        xml_data = generate_tally_xml(df_clean, bank_ledger, party_ledger)
                        st.success("Done!")
                        st.download_button("Download XML", xml_data, "tally.xml")
                else:
                    st.error("Format not recognized or password incorrect.")

# --- TAB 2: USER MANAGEMENT (LOGIN & ADMIN) ---
with tabs[1]:
    st.markdown("<br>", unsafe_allow_html=True) # Spacer
    
    if not st.session_state.logged_in:
        # LOGIN SCREEN
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            with st.container(border=True):
                st.markdown("### 🔐 Admin Login")
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                
                if st.button("Login"):
                    user_record = st.session_state.users_db[
                        (st.session_state.users_db['Username'] == username) & 
                        (st.session_state.users_db['Password'] == password)
                    ]
                    
                    if not user_record.empty:
                        st.session_state.logged_in = True
                        st.session_state.current_user = username
                        st.rerun()
                    else:
                        st.error("Invalid Username or Password")
                
                st.info("Default: admin / 123")
    else:
        # DASHBOARD (LOGGED IN)
        st.markdown(f"### 👋 Welcome back, {st.session_state.current_user}!")
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Users", len(st.session_state.users_db))
        m2.metric("Active Sessions", "1")
        m3.metric("System Status", "Online")
        
        st.divider()
        
        c_list, c_add = st.columns([2, 1])
        
        with c_list:
            st.markdown("#### 👥 User List")
            st.dataframe(st.session_state.users_db[["Username", "Role", "Status"]], use_container_width=True)
        
        with c_add:
            with st.container(border=True):
                st.markdown("#### ➕ Add New User")
                new_user = st.text_input("New Username")
                new_pass = st.text_input("New Password", type="password")
                new_role = st.selectbox("Role", ["User", "Admin"])
                
                if st.button("Create User"):
                    new_entry = pd.DataFrame([{"Username": new_user, "Password": new_pass, "Role": new_role, "Status": "Active"}])
                    st.session_state.users_db = pd.concat([st.session_state.users_db, new_entry], ignore_index=True)
                    st.success("User Added!")
                    st.rerun()

        if st.button("Logout"):
            st.session_state.logged_in = False
            st.rerun()

# --- TAB 3: PRICING (STATIC) ---
with tabs[2]:
    st.markdown("<br><br><h2 style='text-align:center'>Simple, Transparent Pricing</h2>", unsafe_allow_html=True)
    p1, p2, p3 = st.columns(3)
    
    with p2:
        with st.container(border=True):
            st.markdown("""
                <h3 style='text-align:center'>Pro Plan</h3>
                <h1 style='text-align:center; color:#0044CC'>$19<span style='font-size:1rem'>/mo</span></h1>
                <ul>
                    <li>Unlimited PDF Conversions</li>
                    <li>24/7 Support</li>
                    <li>Advanced User Management</li>
                </ul>
            """, unsafe_allow_html=True)
            st.button("Start Free Trial", use_container_width=True)

# --- FOOTER ---
try: footer_logo_b64 = get_img_as_base64("logo 1.png")
except: footer_logo_b64 = None
footer_html = f'<img src="data:image/png;base64,{footer_logo_b64}" width="25">' if footer_logo_b64 else ""

st.markdown(f"""
    <div class="footer">
        <p>Sponsored By {footer_html} <span style="color:#0044CC; font-weight:700">Uday Mondal</span> | Consultant Advocate</p>
        <p style="font-size: 13px;">Powered & Created by <span style="color:#0044CC; font-weight:700">Debasish Biswas</span></p>
    </div>
""", unsafe_allow_html=True)
