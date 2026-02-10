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

# --- 2. SESSION STATE (DATABASE & LOGIN) ---
if 'users_db' not in st.session_state:
    st.session_state.users_db = pd.DataFrame([
        {"Username": "admin", "Password": "123", "Role": "Admin", "Status": "Active"},
        {"Username": "uday", "Password": "123", "Role": "User", "Status": "Active"}
    ])

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.current_user = None

# --- 3. CUSTOM CSS (BLUE HEADER + PINNED FOOTER) ---
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
        
        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif;
            background-color: #FFFFFF;
            color: #0F172A;
            margin-bottom: 100px; /* Space for footer */
        }

        /* --- NAVBAR --- */
        .stTabs {
            background-color: #0056D2; /* Header Blue */
            padding-top: 10px;
            padding-bottom: 0px;
            margin-top: -6rem; 
            position: sticky;
            top: 0;
            z-index: 999;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }

        .stTabs [data-baseweb="tab-list"] {
            gap: 20px;
            justify-content: flex-end;
            padding-right: 40px;
        }

        .stTabs [data-baseweb="tab"] {
            height: 55px;
            white-space: pre-wrap;
            background-color: transparent;
            border: none;
            color: rgba(255, 255, 255, 0.9);
            font-weight: 500;
            font-size: 1rem;
        }

        .stTabs [data-baseweb="tab"]:hover {
            color: #FFFFFF;
        }

        .stTabs [aria-selected="true"] {
            background-color: rgba(255, 255, 255, 0.15) !important;
            color: #FFFFFF !important;
            border-bottom: 4px solid #66E035; /* Green Active Line */
            font-weight: 700;
        }

        /* --- HERO SECTION --- */
        .hero-container {
            background-color: #0056D2;
            color: white;
            padding: 50px 60px 80px 60px;
            margin: 0 -4rem 0 -4rem;
        }
        
        .hero-title {
            font-size: 3rem;
            font-weight: 800;
            line-height: 1.1;
            margin-bottom: 20px;
            color: white !important;
        }
        
        .hero-subtitle {
            font-size: 1.2rem;
            opacity: 0.9;
            margin-bottom: 30px;
            line-height: 1.6;
            color: #E0E7FF !important;
        }

        /* --- CONTENT CARDS --- */
        .content-card {
            background-color: white;
            padding: 30px;
            border-radius: 12px;
            border: 1px solid #E2E8F0;
            box-shadow: 0 4px 6px rgba(0,0,0,0.05);
            margin-bottom: 20px;
        }
        
        .card-title {
            color: #0056D2;
            font-weight: 700;
            font-size: 1.2rem;
            margin-bottom: 10px;
        }

        /* --- BUTTONS --- */
        div[data-testid="stButton"] button {
            background-color: #66E035; /* Bright Green */
            color: #0056D2;
            font-weight: 700;
            border-radius: 50px;
            border: none;
            width: 100%;
            padding: 10px 20px;
        }
        div[data-testid="stButton"] button:hover {
            background-color: #5AC72E;
            color: white;
        }

        /* --- PINNED FOOTER --- */
        .footer {
            position: fixed;
            left: 0;
            bottom: 0;
            width: 100%;
            background-color: #FFFFFF;
            color: #64748B;
            text-align: center;
            padding: 15px;
            border-top: 1px solid #E2E8F0;
            z-index: 1000;
            font-size: 14px;
            box-shadow: 0 -2px 10px rgba(0,0,0,0.05);
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

def extract_data_from_pdf(file, password=None):
    all_rows = []
    try:
        pwd = password if password else None
        with pdfplumber.open(file, password=pwd) as pdf:
            for page in pdf.pages:
                table = page.extract_table()
                if table:
                    for row in table:
                        cleaned_row = [str(cell).replace('\n', ' ').strip() if cell else '' for cell in row]
                        if any(cleaned_row):
                            all_rows.append(cleaned_row)
        if not all_rows: return None
        df = pd.DataFrame(all_rows)
        header_idx = 0
        found_header = False
        for i, row in df.iterrows():
            row_str = row.astype(str).str.lower().values
            if any('date' in x for x in row_str) and \
               (any('balance' in x for x in row_str) or any('debit' in x for x in row_str)):
                header_idx = i
                found_header = True
                break
        if found_header:
            new_header = df.iloc[header_idx]
            df = df[header_idx + 1:] 
            df.columns = new_header
        return df
    except Exception as e:
        return None

def load_bank_file(file, password=None):
    if file.name.lower().endswith('.pdf'):
        return extract_data_from_pdf(file, password)
    else: 
        try:
            return pd.read_excel(file)
        except: return None

def normalize_bank_data(df, bank_name):
    target_columns = ['Date', 'Narration', 'Debit', 'Credit']
    df.columns = df.columns.astype(str).str.replace('\n', ' ').str.strip()
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
        debit_amt, credit_amt = row['Debit'], row['Credit']
        if debit_amt > 0: vch_type, amount, l1, l2 = "Payment", debit_amt, default_party_ledger, bank_ledger_name
        elif credit_amt > 0: vch_type, amount, l1, l2 = "Receipt", credit_amt, bank_ledger_name, default_party_ledger
        else: continue
        try: date_str = pd.to_datetime(row['Date'], dayfirst=True).strftime("%Y%m%d")
        except: date_str = "20240401"
        narration = str(row['Narration']).replace("&", "&amp;").replace("<", "&lt;")
        xml_body += f"""<TALLYMESSAGE xmlns:UDF="TallyUDF"><VOUCHER VCHTYPE="{vch_type}" ACTION="Create" OBJVIEW="Accounting Voucher View"><DATE>{date_str}</DATE><NARRATION>{narration}</NARRATION><VOUCHERTYPENAME>{vch_type}</VOUCHERTYPENAME><ALLLEDGERENTRIES.LIST><LEDGERNAME>{l1}</LEDGERNAME><ISDEEMEDPOSITIVE>Yes</ISDEEMEDPOSITIVE><AMOUNT>{-amount}</AMOUNT></ALLLEDGERENTRIES.LIST><ALLLEDGERENTRIES.LIST><LEDGERNAME>{l2}</LEDGERNAME><ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE><AMOUNT>{amount}</AMOUNT></ALLLEDGERENTRIES.LIST></VOUCHER></TALLYMESSAGE>"""
    return f"<ENVELOPE><HEADER><TALLYREQUEST>Import Data</TALLYREQUEST></HEADER><BODY><IMPORTDATA><REQUESTDESC><REPORTNAME>Vouchers</REPORTNAME></REQUESTDESC><REQUESTDATA>{xml_body}</REQUESTDATA></IMPORTDATA></BODY></ENVELOPE>"

# --- 5. NAVIGATION ---
tabs = st.tabs(["Home", "Solutions", "Pricing", "Login", "Register"])

# --- TAB 1: HOME ---
with tabs[0]:
    with st.container():
        st.markdown('<div class="hero-container">', unsafe_allow_html=True)
        
        if st.session_state.logged_in:
            st.markdown(f"## Welcome back, {st.session_state.current_user}!")
            st.markdown("Your Accounting Dashboard is ready below.")
        else:
            col_hero_left, col_hero_right = st.columns([1.5, 1], gap="large")
            with col_hero_left:
                st.markdown("""
                    <div class="hero-title">Perfecting the Science of Data Extraction</div>
                    <div class="hero-subtitle">
                        AI-powered tool to convert bank statements, credit card bills, and financial documents into Tally XML with 99% accuracy.
                    </div>
                """, unsafe_allow_html=True)
                try: hero_logo_b64 = get_img_as_base64("logo.png")
                except: hero_logo_b64 = None
                if hero_logo_b64:
                    st.markdown(f'<img src="data:image/png;base64,{hero_logo_b64}" width="150" style="margin-top:20px;">', unsafe_allow_html=True)

            with col_hero_right:
                # Login/Register Box on Home
                st.markdown('<div class="content-card">', unsafe_allow_html=True)
                st.markdown('<div class="card-title">🚀 Start Free Trial</div>', unsafe_allow_html=True)
                
                auth_mode = st.radio("Choose:", ["Login", "Register"], horizontal=True, label_visibility="collapsed")
                st.write("")
                
                if auth_mode == "Login":
                    u = st.text_input("Username", key="home_u")
                    p = st.text_input("Password", type="password", key="home_p")
                    if st.button("Sign In"):
                        user = st.session_state.users_db[(st.session_state.users_db['Username'] == u) & (st.session_state.users_db['Password'] == p)]
                        if not user.empty:
                            st.session_state.logged_in = True
                            st.session_state.current_user = u
                            st.rerun()
                        else: st.error("Incorrect credentials.")
                else:
                    new_u = st.text_input("New Username", key="home_reg_u")
                    new_p = st.text_input("New Password", type="password", key="home_reg_p")
                    if st.button("Create Account"):
                        if new_u and new_p:
                            if new_u in st.session_state.users_db['Username'].values:
                                st.error("User exists.")
                            else:
                                new_entry = pd.DataFrame([{"Username": new_u, "Password": new_p, "Role": "User", "Status": "Active"}])
                                st.session_state.users_db = pd.concat([st.session_state.users_db, new_entry], ignore_index=True)
                                st.success("Account created! Login now.")
                        else: st.warning("Fill all details.")
                st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # MAIN TOOL (Visible only if Logged In)
    if st.session_state.logged_in:
        st.markdown("<br>", unsafe_allow_html=True)
        c1, c2 = st.columns([1, 1.5], gap="large")
        
        with c1:
            with st.container(border=True):
                st.markdown("### 🛠️ Configuration")
                uploaded_html = st.file_uploader("Upload Tally Master (Optional)", type=['html', 'htm'])
                ledger_list = ["Suspense A/c", "Cash", "Bank"]
                if uploaded_html:
                    extracted = get_ledger_names(uploaded_html)
                    if extracted:
                        ledger_list = extracted
                        st.success(f"✅ Synced {len(ledger_list)} ledgers")
                bank_ledger = st.selectbox("Select Bank Ledger", ledger_list, index=0)
                party_ledger = st.selectbox("Select Default Party", ledger_list, index=0)

        with c2:
            with st.container(border=True):
                st.markdown("### 📂 Upload & Convert")
                col_a, col_b = st.columns(2)
                with col_a: bank_choice = st.selectbox("Bank Format", ["SBI", "PNB", "ICICI", "Axis Bank", "HDFC Bank", "Kotak Mahindra", "Yes Bank", "Indian Bank", "India Post (IPPB)", "RBL Bank", "Other"])
                with col_b: pdf_pass = st.text_input("PDF Password", type="password", placeholder="(Optional)")

                uploaded_file = st.file_uploader("Upload Statement", type=['xlsx', 'xls', 'pdf'])
                if uploaded_file:
                    with st.spinner("Processing..."):
                        df_raw = load_bank_file(uploaded_file, pdf_pass)
                    if df_raw is not None:
                        df_clean = normalize_bank_data(df_raw, bank_choice)
                        st.dataframe(df_clean.head(3), use_container_width=True, hide_index=True)
                        if st.button("🚀 Convert to Tally XML"):
                            xml_data = generate_tally_xml(df_clean, bank_ledger, party_ledger)
                            st.balloons()
                            st.download_button("Download XML", xml_data, "tally_import.xml")
                    else: st.error("Error reading file.")

# --- TAB 2: SOLUTIONS ---
with tabs[1]:
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("## 💡 Our Solutions")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="content-card">', unsafe_allow_html=True)
        st.markdown('<div class="card-title">🤖 Automated Extraction</div>', unsafe_allow_html=True)
        st.write("Stop manual data entry. Our AI automatically detects transaction tables in PDFs and Excel files with 99% accuracy.")
        st.markdown('</div>', unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="content-card">', unsafe_allow_html=True)
        st.markdown('<div class="card-title">🔒 Secure Processing</div>', unsafe_allow_html=True)
        st.write("Your financial data is processed locally within your session. No data is stored on our servers permanently.")
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="content-card">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">🏦 Universal Bank Support</div>', unsafe_allow_html=True)
    st.write("We support SBI, HDFC, ICICI, Axis, PNB, Kotak, Yes Bank, and many more. If your bank isn't listed, our 'Other' format adapts automatically.")
    st.markdown('</div>', unsafe_allow_html=True)

# --- TAB 3: PRICING ---
with tabs[2]:
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("## 💎 Pricing Plans")
    p1, p2, p3 = st.columns(3)
    
    with p1:
        st.markdown("""
        <div class="content-card" style="text-align:center;">
            <h3>Starter</h3>
            <h1 style="color:#0056D2;">Free</h1>
            <p>Perfect for trying out.</p>
            <hr>
            <p>5 Conversions / mo</p>
            <p>Basic Support</p>
            <p>PDF & Excel</p>
        </div>
        """, unsafe_allow_html=True)
    
    with p2:
        st.markdown("""
        <div class="content-card" style="text-align:center; border: 2px solid #0056D2;">
            <h3>Professional</h3>
            <h1 style="color:#0056D2;">₹499<small>/mo</small></h1>
            <p>For Accountants.</p>
            <hr>
            <p>Unlimited Conversions</p>
            <p>Priority Support</p>
            <p>All Bank Formats</p>
        </div>
        """, unsafe_allow_html=True)
    
    with p3:
        st.markdown("""
        <div class="content-card" style="text-align:center;">
            <h3>Enterprise</h3>
            <h1 style="color:#0056D2;">Custom</h1>
            <p>For CA Firms.</p>
            <hr>
            <p>Multi-User Access</p>
            <p>API Integration</p>
            <p>Dedicated Manager</p>
        </div>
        """, unsafe_allow_html=True)

# --- TAB 4 & 5: LOGIN & REGISTER (Direct Access) ---
with tabs[3]:
    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1, 1])
    with c2:
        st.markdown('<div class="content-card">', unsafe_allow_html=True)
        st.markdown("### 🔐 Login")
        u = st.text_input("Username", key="tab_login_u")
        p = st.text_input("Password", type="password", key="tab_login_p")
        if st.button("Secure Login"):
            user = st.session_state.users_db[(st.session_state.users_db['Username'] == u) & (st.session_state.users_db['Password'] == p)]
            if not user.empty:
                st.session_state.logged_in = True
                st.session_state.current_user = u
                st.success("Success! Go to Home.")
            else: st.error("Failed.")
        st.markdown('</div>', unsafe_allow_html=True)

with tabs[4]:
    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1, 1])
    with c2:
        st.markdown('<div class="content-card">', unsafe_allow_html=True)
        st.markdown("### 📝 Register")
        nu = st.text_input("Choose Username", key="tab_reg_u")
        np = st.text_input("Choose Password", type="password", key="tab_reg_p")
        if st.button("Sign Up Free"):
            if nu and np:
                new_entry = pd.DataFrame([{"Username": nu, "Password": np, "Role": "User", "Status": "Active"}])
                st.session_state.users_db = pd.concat([st.session_state.users_db, new_entry], ignore_index=True)
                st.success("Registered! You can now Login.")
            else: st.warning("Fill details.")
        st.markdown('</div>', unsafe_allow_html=True)

# --- PINNED FOOTER ---
try: footer_logo_b64 = get_img_as_base64("logo 1.png")
except: footer_logo_b64 = None
footer_html = f'<img src="data:image/png;base64,{footer_logo_b64}" width="25" style="vertical-align: middle;">' if footer_logo_b64 else ""

st.markdown(f"""
    <div class="footer">
        <p>Sponsored By {footer_html} <span style="color:#0056D2; font-weight:700">Uday Mondal</span> | Consultant Advocate</p>
        <p style="font-size: 13px;">Powered & Created by <span style="color:#0056D2; font-weight:700">Debasish Biswas</span></p>
    </div>
""", unsafe_allow_html=True)
