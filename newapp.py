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

# --- 3. CAELUM-STYLE CSS (BLUE HEADER / WHITE BODY) ---
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
        
        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif;
            background-color: #FFFFFF; 
            color: #0F172A;
        }

        /* --- NAVBAR --- */
        .stTabs {
            background-color: #0044CC; /* Caelum Blue */
            padding-top: 10px;
            padding-bottom: 20px;
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
            height: 50px;
            white-space: pre-wrap;
            background-color: transparent;
            border: none;
            color: rgba(255, 255, 255, 0.9);
            font-weight: 500;
            font-size: 1rem;
        }

        .stTabs [data-baseweb="tab"]:hover { color: #FFFFFF; }

        .stTabs [aria-selected="true"] {
            background-color: #003399 !important; /* Slightly darker active tab */
            color: #FFFFFF !important;
            border-radius: 50px;
            padding: 0 20px;
        }

        /* --- HERO HEADER (BLUE) --- */
        .hero-container {
            background-color: #0044CC; /* Match Navbar */
            padding: 40px 80px 80px 80px;
            margin: -20px -4rem 40px -4rem; /* Extend full width */
            text-align: left;
            border-bottom: 10px solid #F1F5F9; /* Slight separation */
        }
        
        .hero-title { 
            font-size: 3rem; 
            font-weight: 800; 
            color: #FFFFFF !important;
            margin-bottom: 15px;
        }
        
        .hero-subtitle { 
            font-size: 1.2rem; 
            color: #E0E7FF !important; 
            max-width: 600px; 
            line-height: 1.5;
        }

        /* --- MAIN CONTENT AREA (WHITE) --- */
        /* Card Styling for Login/Register Box */
        .auth-card {
            background-color: white;
            padding: 30px;
            border: 1px solid #E2E8F0;
            border-radius: 8px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        }

        /* Streamlit Container override */
        .stContainer {
            background-color: white;
            border: 1px solid #E2E8F0;
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.02);
        }

        /* Buttons (Green Action) */
        div[data-testid="stButton"] button {
             background-color: #4ADE80; /* Caelum Green */
             color: #0044CC; 
             font-weight: 700;
             border-radius: 50px;
             border: none;
             padding: 10px 25px;
             width: 100%;
        }
        div[data-testid="stButton"] button:hover {
             background-color: #22c55e;
             color: white;
        }

        /* Footer */
        .footer {
            margin-top: 80px; padding: 40px; text-align: center; 
            color: #64748B; border-top: 1px solid #E2E8F0;
            background-color: #F8FAFC; margin-bottom: -60px;
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
        mapping = mappings[bank_name]
        df = df.rename(columns=mapping)
    
    for col in target_columns:
        if col not in df.columns: df[col] = 0 if col in ['Debit', 'Credit'] else ""
            
    df['Debit'] = df['Debit'].apply(clean_currency)
    df['Credit'] = df['Credit'].apply(clean_currency)
    df['Narration'] = df['Narration'].fillna('')
    return df[target_columns]

def generate_tally_xml(df, bank_ledger_name, default_party_ledger):
    xml_header = """<ENVELOPE>
    <HEADER><TALLYREQUEST>Import Data</TALLYREQUEST></HEADER>
    <BODY><IMPORTDATA><REQUESTDESC><REPORTNAME>Vouchers</REPORTNAME></REQUESTDESC><REQUESTDATA>"""
    xml_footer = """</REQUESTDATA></IMPORTDATA></BODY></ENVELOPE>"""
    
    xml_body = ""
    for index, row in df.iterrows():
        debit_amt = row['Debit']
        credit_amt = row['Credit']
        
        if debit_amt > 0:
            vch_type = "Payment"
            amount = debit_amt
            led_1_name, led_1_amt, led_1_pos = default_party_ledger, -amount, "Yes"
            led_2_name, led_2_amt, led_2_pos = bank_ledger_name, amount, "No"
        elif credit_amt > 0:
            vch_type = "Receipt"
            amount = credit_amt
            led_1_name, led_1_amt, led_1_pos = bank_ledger_name, -amount, "Yes"
            led_2_name, led_2_amt, led_2_pos = default_party_ledger, amount, "No"
        else: continue

        try:
            date_obj = pd.to_datetime(row['Date'], dayfirst=True)
            date_str = date_obj.strftime("%Y%m%d")
        except: date_str = "20240401"
            
        narration = str(row['Narration']).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

        xml_body += f"""<TALLYMESSAGE xmlns:UDF="TallyUDF">
         <VOUCHER VCHTYPE="{vch_type}" ACTION="Create" OBJVIEW="Accounting Voucher View">
          <DATE>{date_str}</DATE>
          <NARRATION>{narration}</NARRATION>
          <VOUCHERTYPENAME>{vch_type}</VOUCHERTYPENAME>
          <ALLLEDGERENTRIES.LIST>
           <LEDGERNAME>{led_1_name}</LEDGERNAME>
           <ISDEEMEDPOSITIVE>{led_1_pos}</ISDEEMEDPOSITIVE>
           <AMOUNT>{led_1_amt}</AMOUNT>
          </ALLLEDGERENTRIES.LIST>
          <ALLLEDGERENTRIES.LIST>
           <LEDGERNAME>{led_2_name}</LEDGERNAME>
           <ISDEEMEDPOSITIVE>{led_2_pos}</ISDEEMEDPOSITIVE>
           <AMOUNT>{led_2_amt}</AMOUNT>
          </ALLLEDGERENTRIES.LIST>
         </VOUCHER>
        </TALLYMESSAGE>"""
    return xml_header + xml_body + xml_footer

# --- 5. NAVIGATION ---
tabs = st.tabs(["Home", "Solutions", "Pricing", "User Management"])

# --- TAB 1: HOME ---
with tabs[0]:
    # BLUE HERO SECTION
    st.markdown("""
        <div class="hero-container">
            <div class="hero-title">Perfecting the Science of Data Extraction</div>
            <div class="hero-subtitle">
                AI-powered tool to convert bank statements and financial documents into Tally XML with 99% accuracy. 
                Supports Excel & PDF formats.
            </div>
        </div>
    """, unsafe_allow_html=True)

    if st.session_state.logged_in:
        # LOGGED IN: SHOW DASHBOARD
        st.markdown("### 🚀 Dashboard")
        
        col_left, col_right = st.columns([1, 1.5], gap="large")
        
        with col_left:
            with st.container():
                st.markdown("#### 🛠️ Settings & Mapping")
                uploaded_html = st.file_uploader("Upload Tally Master (Optional)", type=['html', 'htm'])
                
                ledger_list = ["Suspense A/c", "Cash", "Bank"]
                if uploaded_html:
                    extracted = get_ledger_names(uploaded_html)
                    if extracted:
                        ledger_list = extracted
                        st.success(f"✅ Synced {len(ledger_list)} ledgers")
                
                bank_ledger = st.selectbox("Select Bank Ledger", ledger_list, index=0)
                party_ledger = st.selectbox("Select Default Party", ledger_list, index=0)

        with col_right:
            with st.container():
                st.markdown("#### 📂 Upload & Convert")
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
                            st.download_button("Download XML File", xml_data, "tally_import.xml", "application/xml")
                    else:
                        st.error("⚠️ Error: Could not read file. Check format or password.")

    else:
        # NOT LOGGED IN: SHOW LANDING PAGE (Image Left, Login Right)
        col1, col2 = st.columns([1.5, 1], gap="large")
        
        with col1:
            try: hero_logo_b64 = get_img_as_base64("logo.png")
            except: hero_logo_b64 = None
            hero_img_html = f'<img src="data:image/png;base64,{hero_logo_b64}" style="width: 80%; display:block; margin:auto;">' if hero_logo_b64 else ""
            st.markdown(f"{hero_img_html}", unsafe_allow_html=True)
            
            st.markdown("""
            <div style="margin-top:20px; color:#475569;">
                <h3>Why Choose Accounting Expert?</h3>
                <ul>
                    <li><strong>99% Accuracy:</strong> AI-powered extraction.</li>
                    <li><strong>Secure:</strong> Data processed locally.</li>
                    <li><strong>Universal:</strong> Supports most Indian banks.</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown('<div class="auth-card">', unsafe_allow_html=True)
            auth_mode = st.radio("Access Tool:", ["Register for Free Trial", "Login"], horizontal=True)
            st.write("")
            
            if auth_mode == "Login":
                u = st.text_input("Username", key="login_u")
                p = st.text_input("Password", type="password", key="login_p")
                if st.button("Sign In"):
                    user = st.session_state.users_db[(st.session_state.users_db['Username'] == u) & (st.session_state.users_db['Password'] == p)]
                    if not user.empty:
                        st.session_state.logged_in = True
                        st.session_state.current_user = u
                        st.rerun()
                    else: st.error("Incorrect credentials.")
            else:
                new_u = st.text_input("Create Username", key="reg_u")
                new_p = st.text_input("Create Password", type="password", key="reg_p")
                if st.button("Start Free Trial"):
                    if new_u and new_p:
                        if new_u in st.session_state.users_db['Username'].values:
                            st.error("User exists.")
                        else:
                            new_entry = pd.DataFrame([{"Username": new_u, "Password": new_p, "Role": "User", "Status": "Active"}])
                            st.session_state.users_db = pd.concat([st.session_state.users_db, new_entry], ignore_index=True)
                            st.success("Created! Please Login.")
                    else: st.warning("Fill all details.")
            st.markdown('</div>', unsafe_allow_html=True)

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
footer_html = f'<img src="data:image/png;base64,{footer_logo_b64}" width="25" style="vertical-align: middle;">' if footer_logo_b64 else ""

st.markdown(f"""
    <div class="footer">
        <p>Sponsored By {footer_html} <span style="color:#0044CC; font-weight:700">Uday Mondal</span> | Consultant Advocate</p>
        <p style="font-size: 13px;">Powered & Created by <span style="color:#0044CC; font-weight:700">Debasish Biswas</span></p>
    </div>
""", unsafe_allow_html=True)
