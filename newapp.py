import streamlit as st
import pandas as pd
from PIL import Image
from bs4 import BeautifulSoup
import pdfplumber
import io
import base64

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Accounting Expert | AI Bank to Tally",
    page_icon="logo.png",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 2. SESSION STATE (DATABASE & LOGIN) ---
if 'users_db' not in st.session_state:
    st.session_state.users_db = pd.DataFrame([
        {"Username": "admin", "Password": "123", "Role": "Admin", "Status": "Active"},
        {"Username": "uday", "Password": "123", "Role": "User", "Status": "Active"}
    ])

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.current_user = None

# --- 3. CAELUM-STYLE CSS ---
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
        
        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif;
            background-color: #F8FAFC; 
            color: #0F172A;
        }

        /* --- NAVBAR / TABS STYLING --- */
        .stTabs {
            background-color: #0044CC; /* Caelum Blue */
            padding-top: 10px;
            padding-bottom: 0px;
            margin-top: -6rem; 
            position: sticky;
            top: 0;
            z-index: 999;
        }

        .stTabs [data-baseweb="tab-list"] {
            gap: 25px;
            justify-content: flex-end;
            padding-right: 50px;
        }

        .stTabs [data-baseweb="tab"] {
            height: 60px;
            white-space: pre-wrap;
            background-color: transparent;
            border: none;
            color: rgba(255, 255, 255, 0.8);
            font-weight: 500;
            font-size: 1rem;
        }

        .stTabs [data-baseweb="tab"]:hover {
            color: #FFFFFF;
        }

        .stTabs [aria-selected="true"] {
            background-color: transparent !important;
            color: #FFFFFF !important;
            border-bottom: 4px solid #4ADE80; /* Green Active Indicator */
            font-weight: 700;
        }

        /* --- HERO SECTION --- */
        .hero-section {
            background-color: #0044CC; /* Blue Background */
            padding: 60px 80px 100px 80px;
            margin: 0 -4rem 30px -4rem;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        
        /* FORCE WHITE TEXT FOR HERO */
        .hero-title { 
            font-size: 3.5rem; 
            font-weight: 800; 
            line-height: 1.1; 
            margin-bottom: 20px; 
            color: #FFFFFF !important;
        }
        
        .hero-subtitle { 
            font-size: 1.2rem; 
            color: #E0E7FF !important;
            margin-bottom: 30px; 
            max-width: 600px; 
            line-height: 1.6;
        }
        
        /* CARD STYLING */
        .stContainer {
            background-color: white;
            padding: 30px;
            border-radius: 12px;
            box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);
            border: 1px solid #E2E8F0;
        }
        
        /* Buttons */
        div[data-testid="stButton"] button {
             background-color: #4ADE80; /* Caelum Green */
             color: #0044CC; 
             font-weight: 700;
             border-radius: 50px;
             border: none;
             padding: 10px 25px;
        }
        div[data-testid="stButton"] button:hover {
             background-color: #22c55e;
             color: white;
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
        if not ledgers:
            all_text = soup.get_text(separator='\n')
            lines = [line.strip() for line in all_text.split('\n') if line.strip()]
            ledgers = sorted(list(set(lines)))
        return sorted(ledgers)
    except: return []

def clean_currency(value):
    if pd.isna(value) or value == '': return 0.0
    val_str = str(value).replace(',', '').strip()
    try: return float(val_str)
    except: return 0.0

def load_bank_file(file, password=None):
    if file.name.lower().endswith('.pdf'):
        all_rows = []
        try:
            pwd = password if password else None
            with pdfplumber.open(file, password=pwd) as pdf:
                for page in pdf.pages:
                    table = page.extract_table()
                    if table:
                        for row in table:
                            cleaned = [str(cell).replace('\n', ' ').strip() if cell else '' for cell in row]
                            if any(cleaned): all_rows.append(cleaned)
            if not all_rows: return None
            df = pd.DataFrame(all_rows)
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
        'Kotak Mahindra': {'Transaction Date': 'Date', 'Transaction Details': 'Narration', 'Withdrawal Amount': 'Debit', 'Deposit Amount': 'Credit'},
        'Yes Bank': {'Value Date': 'Date', 'Description': 'Narration', 'Debit Amount': 'Debit', 'Credit Amount': 'Credit'},
        'Indian Bank': {'Value Date': 'Date', 'Narration': 'Narration', 'Debit': 'Debit', 'Credit': 'Credit'},
        'India Post (IPPB)': {'Date': 'Date', 'Remarks': 'Narration', 'Debit Amount': 'Debit', 'Credit Amount': 'Credit'},
        'RBL Bank': {'Transaction Date': 'Date', 'Transaction Description': 'Narration', 'Withdrawal Amount': 'Debit', 'Deposit Amount': 'Credit'}
    }
    
    if bank_name in mappings:
        df = df.rename(columns=mappings[bank_name])
    
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

# --- 5. TOP NAVIGATION BAR ---
tabs = st.tabs(["Home", "Solutions", "Pricing", "User Management"])

# --- TAB 1: HOME (CONVERTER) ---
with tabs[0]:
    # Hero Section
    try: hero_logo_b64 = get_img_as_base64("logo.png")
    except: hero_logo_b64 = None
    hero_img_html = f'<img src="data:image/png;base64,{hero_logo_b64}" style="max-width: 100%; animation: float 6s ease-in-out infinite;">' if hero_logo_b64 else ""

    st.markdown(f"""
        <div class="hero-section">
            <div class="hero-content">
                <div class="hero-title">Perfecting the Science of Data Extraction</div>
                <div class="hero-subtitle">
                    AI-powered tool to convert bank statements, financial documents into Tally XML with 99% accuracy. 
                    Supports Excel & PDF formats.
                </div>
            </div>
            <div style="width: 250px;">{hero_img_html}</div>
        </div>
    """, unsafe_allow_html=True)

    # --- MAIN CONTENT AREA ---
    if st.session_state.logged_in:
        # LOGGED IN: SHOW THE TOOL
        col_left, col_right = st.columns([1, 1.5], gap="large")
        
        with col_left:
            with st.container(border=True):
                st.markdown("### 🛠️ 1. Settings & Mapping")
                uploaded_html = st.file_uploader("Upload Tally Master (Optional)", type=['html', 'htm'], help="Upload 'List of Accounts.html' exported from Tally.")
                
                ledger_list = ["Suspense A/c", "Cash", "Bank"]
                if uploaded_html:
                    extracted = get_ledger_names(uploaded_html)
                    if extracted:
                        ledger_list = extracted
                        st.success(f"✅ Synced {len(ledger_list)} ledgers")
                
                bank_ledger = st.selectbox("Select Bank Ledger", ledger_list, index=0)
                party_ledger = st.selectbox("Select Default Party", ledger_list, index=0)

        with col_right:
            with st.container(border=True):
                st.markdown("### 📂 2. Upload & Convert")
                c1, c2 = st.columns([1.5, 1])
                with c1: bank_choice = st.selectbox("Bank Format", ["SBI", "PNB", "ICICI", "Axis Bank", "HDFC Bank", "Kotak Mahindra", "Yes Bank", "Indian Bank", "India Post (IPPB)", "RBL Bank", "Other"])
                with c2: pdf_pass = st.text_input("PDF Password", type="password", placeholder="(Optional)")

                uploaded_file = st.file_uploader("Upload Statement (Excel or PDF)", type=['xlsx', 'xls', 'pdf'])
                
                if uploaded_file:
                    with st.spinner("Processing..."):
                        df_raw = load_bank_file(uploaded_file, pdf_pass)
                    
                    if df_raw is not None:
                        df_clean = normalize_bank_data(df_raw, bank_choice)
                        st.dataframe(df_clean.head(3), use_container_width=True, hide_index=True)
                        st.write("")
                        if st.button("🚀 Convert to Tally XML"):
                            xml_data = generate_tally_xml(df_clean, bank_ledger, party_ledger)
                            st.balloons()
                            st.success("Conversion Successful!")
                            st.download_button("Download XML File", xml_data, "tally_import.xml")
                    else:
                        st.error("⚠️ Error: Could not read file. Check format or password.")
    
    else:
        # --- NOT LOGGED IN: SHOW REGISTER/LOGIN FORM ---
        c1, c2 = st.columns([1, 1])
        
        with c1:
            st.markdown("### Why Choose Accounting Expert?")
            st.info("""
            ✅ **99% Accuracy** with AI-powered extraction.  
            ✅ **Supports PDF & Excel** statements.  
            ✅ **Instant Tally XML** generation.  
            ✅ **Secure & Private** processing.
            """)
        
        with c2:
            with st.container(border=True):
                # Simple Toggle for Login/Register on Home Page
                auth_mode = st.radio("Access Tool:", ["Register for Free Trial", "Login"], horizontal=True)
                st.divider()
                
                if auth_mode == "Login":
                    u = st.text_input("Username", key="home_login_u")
                    p = st.text_input("Password", type="password", key="home_login_p")
                    if st.button("Access Dashboard"):
                        user = st.session_state.users_db[(st.session_state.users_db['Username'] == u) & (st.session_state.users_db['Password'] == p)]
                        if not user.empty:
                            st.session_state.logged_in = True
                            st.session_state.current_user = u
                            st.rerun()
                        else: st.error("Incorrect username or password.")
                else:
                    new_u = st.text_input("Create Username", key="home_reg_u")
                    new_p = st.text_input("Create Password", type="password", key="home_reg_p")
                    if st.button("Start Free Trial"):
                        if new_u and new_p:
                             if new_u in st.session_state.users_db['Username'].values:
                                st.error("User already exists.")
                             else:
                                new_entry = pd.DataFrame([{"Username": new_u, "Password": new_p, "Role": "User", "Status": "Active"}])
                                st.session_state.users_db = pd.concat([st.session_state.users_db, new_entry], ignore_index=True)
                                st.success("Account Created! You can now Login.")
                        else: st.warning("Please fill details.")

# --- TAB 2 & 3: PLACEHOLDERS ---
with tabs[1]: st.info("Solutions Page - Coming Soon...")
with tabs[2]: st.info("Pricing Page - Coming Soon...")

# --- TAB 4: USER MANAGEMENT ---
with tabs[3]:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.session_state.logged_in:
        st.success(f"Logged in as: {st.session_state.current_user}")
        if st.button("Logout"):
            st.session_state.logged_in = False
            st.rerun()
        st.divider()
        st.markdown("### 👥 User Database (Admin View)")
        st.dataframe(st.session_state.users_db, use_container_width=True)
    else:
        st.warning("Please Login from the Home Page first.")

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
