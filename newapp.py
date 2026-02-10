import streamlit as st
import pandas as pd
from bs4 import BeautifulSoup
import pdfplumber
import base64

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Accounting Expert | AI Bank to Tally",
    page_icon="logo.png",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 2. CLEAN LIGHT THEME CSS ---
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
        
        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif;
            background-color: #FFFFFF; /* Pure White Background */
            color: #0F172A; /* Dark Slate Text */
        }

        /* --- NAVBAR STYLING --- */
        .stTabs {
            background-color: #0044CC; /* Caelum Blue Navbar Strip */
            padding-top: 10px;
            padding-bottom: 0px;
            margin-top: -6rem; 
            position: sticky;
            top: 0;
            z-index: 999;
            box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
        }

        .stTabs [data-baseweb="tab-list"] {
            gap: 30px;
            justify-content: flex-end;
            padding-right: 50px;
        }

        .stTabs [data-baseweb="tab"] {
            height: 60px;
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
            background-color: transparent !important;
            color: #FFFFFF !important;
            border-bottom: 4px solid #4ADE80; /* Green Active Indicator */
            font-weight: 700;
        }

        /* --- HERO SECTION (LIGHT THEME) --- */
        .hero-section {
            background-color: #F8FAFC; /* Very Light Grey */
            padding: 60px 80px 60px 80px;
            margin: 0 -4rem 30px -4rem;
            display: flex;
            align-items: center;
            justify-content: space-between;
            border-bottom: 1px solid #E2E8F0;
        }
        
        /* Dark Blue Title */
        .hero-title { 
            font-size: 3.5rem; 
            font-weight: 800; 
            line-height: 1.1; 
            margin-bottom: 20px; 
            color: #0044CC !important; 
        }
        
        /* Grey Subtitle */
        .hero-subtitle { 
            font-size: 1.2rem; 
            color: #475569 !important; 
            margin-bottom: 30px; 
            max-width: 600px; 
            line-height: 1.6;
        }
        
        /* CARD STYLING */
        .stContainer {
            background-color: white;
            padding: 30px;
            border-radius: 12px;
            box-shadow: 0 4px 15px -3px rgba(0,0,0,0.05);
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
             transition: all 0.3s ease;
        }
        div[data-testid="stButton"] button:hover {
             background-color: #22c55e;
             color: white;
             transform: translateY(-2px);
             box-shadow: 0 4px 12px rgba(34, 197, 94, 0.4);
        }

        /* Footer */
        .footer {
            margin-top: 60px; padding: 40px; text-align: center; 
            color: #64748B; border-top: 1px solid #E2E8F0;
            background-color: #F8FAFC; margin-bottom: -60px;
        }
        
        #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- 3. LOGIC FUNCTIONS ---
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

# --- 4. TOP NAVIGATION BAR ---
tabs = st.tabs(["Home", "Solutions", "Pricing"])

# --- TAB 1: HOME ---
with tabs[0]:
    # LIGHT THEME HERO SECTION
    # Using 'logo.png' for the hero illustration
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

    # --- MAIN TOOL AREA (OPEN TO ALL) ---
    col_left, col_right = st.columns([1, 1.5], gap="large")
    
    with col_left:
        with st.container():
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
        with st.container():
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
                        st.download_button("Download XML File", xml_data, "tally_import.xml", "application/xml")
                else:
                    st.error("⚠️ Error: Could not read file. Check format or password.")

# --- TAB 2 & 3: PLACEHOLDERS ---
with tabs[1]: st.info("Solutions Page - Coming Soon...")
with tabs[2]: st.info("Pricing Page - Coming Soon...")

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
