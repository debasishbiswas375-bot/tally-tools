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

# --- 2. CAELUM.AI EXACT CLONE CSS ---
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
        
        /* Global Settings */
        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif;
            background-color: #F8FAFC; 
            color: #0F172A;
            overflow-x: hidden;
        }

        /* --- NAVIGATION BAR (Mock) --- */
        .nav-container {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 20px 50px;
            background-color: #0044CC; /* Caelum Blue */
            color: white;
            font-size: 0.9rem;
            font-weight: 500;
            margin: -6rem -4rem 0 -4rem; /* Stretch to top */
        }
        .nav-logo {
            font-size: 1.5rem;
            font-weight: 800;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .nav-links {
            display: flex;
            gap: 30px;
            align-items: center;
        }
        .nav-link { color: white; text-decoration: none; opacity: 0.9; cursor: pointer; }
        .nav-link:hover { opacity: 1; text-decoration: underline; }
        
        .nav-btn-login {
            border: 1px solid white;
            padding: 8px 20px;
            border-radius: 50px;
            background: transparent;
            color: white;
            cursor: pointer;
        }
        .nav-btn-trial {
            background-color: #4ADE80; /* Bright Green */
            color: #0044CC;
            padding: 8px 20px;
            border-radius: 50px;
            border: none;
            font-weight: 700;
            cursor: pointer;
        }

        /* --- HERO SECTION --- */
        .hero-section {
            background-color: #0044CC; /* The Main Blue */
            color: white;
            padding: 60px 80px 100px 80px;
            margin: 0 -4rem 30px -4rem;
            display: flex;
            align-items: center;
            justify-content: space-between;
            position: relative;
            overflow: hidden;
        }
        
        /* Background decorative circles (Subtle) */
        .hero-section::before {
            content: '';
            position: absolute;
            width: 400px;
            height: 400px;
            background: rgba(255, 255, 255, 0.03);
            border-radius: 50%;
            top: -100px;
            right: -50px;
        }

        .hero-content {
            max-width: 55%;
            z-index: 2;
        }
        
        .hero-title {
            font-size: 3.5rem;
            font-weight: 800;
            line-height: 1.1;
            margin-bottom: 20px;
        }
        
        .hero-subtitle {
            font-size: 1.1rem;
            opacity: 0.9;
            line-height: 1.6;
            margin-bottom: 30px;
            max-width: 90%;
        }

        .hero-cta {
            background-color: #4ADE80; /* The Green Button */
            color: #0044CC;
            padding: 15px 35px;
            border-radius: 50px;
            font-weight: 700;
            border: none;
            font-size: 1rem;
            display: inline-block;
            box-shadow: 0 4px 15px rgba(74, 222, 128, 0.3);
        }

        .hero-image-container {
            width: 40%;
            display: flex;
            justify-content: center;
            z-index: 2;
        }
        
        .hero-image-container img {
            max-width: 100%;
            filter: drop-shadow(0 10px 20px rgba(0,0,0,0.2));
            animation: float 6s ease-in-out infinite;
        }

        @keyframes float {
            0% { transform: translateY(0px); }
            50% { transform: translateY(-15px); }
            100% { transform: translateY(0px); }
        }

        /* --- MAIN APP CARDS --- */
        .stContainer {
            background-color: white;
            padding: 30px;
            border-radius: 12px;
            box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.05);
            border: 1px solid #E2E8F0;
        }
        
        h3 {
            color: #0F172A !important;
            font-weight: 700 !important;
        }

        /* Streamlit Buttons to match the Green Theme */
        .stButton>button {
            background-color: #0044CC; /* Blue */
            color: white;
            border-radius: 8px;
            height: 50px;
            font-weight: 600;
            border: none;
        }
        .stButton>button:hover {
            background-color: #003399;
        }
        
        /* The GENERATE Button specifically */
        div[data-testid="stButton"] button {
             background-color: #4ADE80 !important; /* Green */
             color: #0044CC !important;
             font-weight: 800 !important;
        }

        /* Footer */
        .footer {
            margin-top: 60px;
            padding: 40px;
            text-align: center;
            color: #64748B;
            font-size: 0.9rem;
            border-top: 1px solid #E2E8F0;
            background-color: white;
            margin-bottom: -60px;
        }
        .brand-link { color: #0044CC; font-weight: 700; text-decoration: none; }
        
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- 3. HELPER FUNCTIONS ---

def get_img_as_base64(file):
    try:
        with open(file, "rb") as f:
            data = f.read()
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

# PDF Extraction
def extract_data_from_pdf(file, password=None):
    all_rows = []
    try:
        with pdfplumber.open(file, password=password) as pdf:
            for page in pdf.pages:
                table = page.extract_table()
                if table:
                    for row in table:
                        cleaned_row = [str(cell).replace('\n', ' ').strip() if cell else '' for cell in row]
                        if any(cleaned_row):
                            all_rows.append(cleaned_row)
        if not all_rows: return None
        df = pd.DataFrame(all_rows)
        
        # Smart Header Detection
        header_idx = 0
        found = False
        for i, row in df.iterrows():
            row_str = row.astype(str).str.lower().values
            if any('date' in x for x in row_str) and \
               (any('balance' in x for x in row_str) or any('debit' in x for x in row_str)):
                header_idx = i
                found = True
                break
        
        if found:
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
        mapping = mappings[bank_name]
        df = df.rename(columns=mapping)
        for col in target_columns:
            if col not in df.columns:
                df[col] = 0 if col in ['Debit', 'Credit'] else ""
        df['Debit'] = df['Debit'].apply(clean_currency)
        df['Credit'] = df['Credit'].apply(clean_currency)
        df['Narration'] = df['Narration'].fillna('')
        return df[target_columns]
    return df

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
            led_1_name, led_1_amt = default_party_ledger, -amount
            led_2_name, led_2_amt = bank_ledger_name, amount
        elif credit_amt > 0:
            vch_type = "Receipt"
            amount = credit_amt
            led_1_name, led_1_amt = bank_ledger_name, -amount
            led_2_name, led_2_amt = default_party_ledger, amount
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
           <ISDEEMEDPOSITIVE>Yes</ISDEEMEDPOSITIVE>
           <AMOUNT>{led_1_amt}</AMOUNT>
          </ALLLEDGERENTRIES.LIST>
          <ALLLEDGERENTRIES.LIST>
           <LEDGERNAME>{led_2_name}</LEDGERNAME>
           <ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE>
           <AMOUNT>{led_2_amt}</AMOUNT>
          </ALLLEDGERENTRIES.LIST>
         </VOUCHER>
        </TALLYMESSAGE>"""
        
    return xml_header + xml_body + xml_footer

# --- 4. HERO SECTION (HTML INJECTION) ---
# Prepare Base64 Image for the Hero Section (Main Logo)
try:
    hero_logo_b64 = get_img_as_base64("logo.png")
    hero_img_html = f'<img src="data:image/png;base64,{hero_logo_b64}" alt="App Logo">'
except: 
    hero_img_html = '<div style="font-size: 100px;">📊</div>'

st.markdown(f"""
    <div class="nav-container">
        <div class="nav-logo">
            <span>Accounting Expert</span>
        </div>
        <div class="nav-links">
            <span class="nav-link">Home</span>
            <span class="nav-link">Solutions</span>
            <span class="nav-link">Pricing</span>
            <span class="nav-link">Contact Sales</span>
            <button class="nav-btn-login">Login</button>
            <button class="nav-btn-trial">Free Trial</button>
        </div>
    </div>

    <div class="hero-section">
        <div class="hero-content">
            <div class="hero-title">Perfecting the Science of Data Extraction</div>
            <div class="hero-subtitle">
                AI-powered tool to convert bank statements, financial documents into Tally XML with 99% accuracy. 
                Supports Excel & PDF formats.
            </div>
            <div class="hero-cta">Sign Up For Free Trial</div>
        </div>
        <div class="hero-image-container">
            {hero_img_html}
        </div>
    </div>
""", unsafe_allow_html=True)

# --- 5. MAIN DASHBOARD ---
col_left, col_right = st.columns([1, 1.5], gap="large")

# LEFT CARD: CONFIGURATION
with col_left:
    with st.container():
        st.markdown("### 🛠️ 1. Settings & Mapping")
        
        uploaded_html = st.file_uploader("Upload Tally Master (Optional)", type=['html', 'htm'])
        ledger_list = ["Suspense A/c", "Cash", "Bank"]
        if uploaded_html:
            extracted = get_ledger_names(uploaded_html)
            if extracted:
                ledger_list = extracted
                st.success(f"✅ Synced {len(ledger_list)} ledgers")
            
        bank_ledger = st.selectbox("Select Bank Ledger", ledger_list, index=0)
        party_ledger = st.selectbox("Select Default Party", ledger_list, index=0)

# RIGHT CARD: ACTION AREA
with col_right:
    with st.container():
        st.markdown("### 📂 2. Upload & Convert")
        
        c1, c2 = st.columns([1.5, 1])
        with c1:
            bank_choice = st.selectbox("Select Bank Format", ["SBI", "PNB", "ICICI", "Axis Bank", "HDFC Bank", "Kotak Mahindra", "Yes Bank", "Indian Bank", "India Post (IPPB)", "RBL Bank", "Other"])
        with c2:
            pdf_password = st.text_input("PDF Password", type="password", placeholder="Optional")

        uploaded_file = st.file_uploader("Drop your Statement here (Excel or PDF)", type=['xlsx', 'xls', 'pdf'])
        
        if uploaded_file:
            st.markdown("---")
            with st.spinner("Analyzing document structure..."):
                df_raw = load_bank_file(uploaded_file, pdf_password)
            
            if df_raw is not None:
                df_clean = normalize_bank_data(df_raw, bank_choice)
                
                st.write("**Data Preview:**")
                st.dataframe(df_clean.head(3), use_container_width=True, hide_index=True)
                
                st.write("")
                # The button here is styled green via CSS above
                if st.button("🚀 Convert to Tally XML"):
                    xml_data = generate_tally_xml(df_clean, bank_ledger, party_ledger)
                    st.balloons()
                    st.success("Conversion Successful! Ready for Import.")
                    st.download_button("⬇️ Download XML File", xml_data, "tally_import.xml", "application/xml")
            else:
                st.error("⚠️ Could not read file. Check format or password.")

# --- 6. FOOTER ---
# Load Uday Mondal's Logo
try:
    footer_logo_b64 = get_img_as_base64("logo 1.png")
except: footer_logo_b64 = None

footer_logo_html = f'<img src="data:image/png;base64,{footer_logo_b64}" width="25" style="vertical-align: middle; margin-right: 8px;">' if footer_logo_b64 else ""

st.markdown(f"""
    <div class="footer">
        <p>Sponsored By {footer_logo_html} <span class="brand-link">Uday Mondal</span> | Consultant Advocate</p>
        <p style="font-size: 13px; margin-top: 8px;">Powered & Created by <span class="brand-link">Debasish Biswas</span> | Professional Tally Automation</p>
    </div>
""", unsafe_allow_html=True)
