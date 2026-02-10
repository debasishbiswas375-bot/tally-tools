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
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 2. CAELUM-STYLE CSS (THE PROFESSIONAL LOOK) ---
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
        
        /* Global Font & Colors */
        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif;
            background-color: #F4F7FC; /* Light Blue-Grey Background */
            color: #0F172A;
        }

        /* Hero Section (Top Banner) */
        .hero-container {
            text-align: center;
            padding: 60px 20px;
            background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
            color: white;
            border-radius: 0px 0px 20px 20px;
            margin-bottom: 30px;
        }
        .hero-title {
            font-size: 3rem;
            font-weight: 700;
            margin-bottom: 10px;
            background: -webkit-linear-gradient(#60A5FA, #3B82F6);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .hero-subtitle {
            font-size: 1.2rem;
            color: #94A3B8;
            font-weight: 300;
        }

        /* Card Styling (White Boxes) */
        .card {
            background-color: white;
            padding: 25px;
            border-radius: 12px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
            border: 1px solid #E2E8F0;
            margin-bottom: 20px;
        }
        .card-header {
            font-size: 1.1rem;
            font-weight: 600;
            color: #334155;
            margin-bottom: 15px;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        /* Button Styling (Caelum Blue) */
        .stButton>button {
            width: 100%;
            background-color: #2563EB; /* Caelum Blue */
            color: white;
            border-radius: 8px;
            height: 50px;
            font-weight: 600;
            border: none;
            transition: all 0.2s;
        }
        .stButton>button:hover {
            background-color: #1D4ED8;
            box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
        }

        /* Success/Info Boxes */
        .stAlert {
            background-color: #EFF6FF;
            border: 1px solid #BFDBFE;
            color: #1E40AF;
        }

        /* Footer Styling */
        .footer {
            margin-top: 50px;
            padding: 20px;
            text-align: center;
            color: #64748B;
            font-size: 0.9rem;
            border-top: 1px solid #E2E8F0;
        }
        .brand-link {
            color: #2563EB;
            text-decoration: none;
            font-weight: 600;
        }
        
        /* Hide Default Streamlit Elements */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- 3. HELPER FUNCTIONS (LOGIC) ---

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

# PDF Extraction Logic
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
    # Standardize Column Names
    df.columns = df.columns.astype(str).str.replace('\n', ' ').str.strip()
    target_columns = ['Date', 'Narration', 'Debit', 'Credit']
    
    mappings = {
        'SBI': {'Txn Date': 'Date', 'Description': 'Narration', 'Debit': 'Debit', 'Credit': 'Credit'},
        'PNB': {'Transaction Date': 'Date', 'Narration': 'Narration', 'Debit Amount': 'Debit', 'Credit Amount': 'Credit'},
        'ICICI': {'Value Date': 'Date', 'Transaction Remarks': 'Narration', 'Withdrawal Amount (INR )': 'Debit', 'Deposit Amount (INR )': 'Credit'},
        'HDFC Bank': {'Date': 'Date', 'Narration': 'Narration', 'Withdrawal Amt.': 'Debit', 'Deposit Amt.': 'Credit'},
        'Axis Bank': {'Tran Date': 'Date', 'Particulars': 'Narration', 'Debit': 'Debit', 'Credit': 'Credit'},
        'Kotak Mahindra': {'Transaction Date': 'Date', 'Transaction Details': 'Narration', 'Withdrawal Amount': 'Debit', 'Deposit Amount': 'Credit'},
        'Yes Bank': {'Value Date': 'Date', 'Description': 'Narration', 'Debit Amount': 'Debit', 'Credit Amount': 'Credit'}
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

# --- 4. HERO SECTION (UI) ---
st.markdown("""
    <div class="hero-container">
        <div class="hero-title">Accounting Expert</div>
        <div class="hero-subtitle">Automate your Tally accounting with AI-powered data extraction.</div>
    </div>
""", unsafe_allow_html=True)

# --- 5. MAIN DASHBOARD ---
col_left, col_right = st.columns([1, 1.5], gap="large")

with col_left:
    st.markdown('<div class="card"><div class="card-header">🛠️ 1. Configuration</div>', unsafe_allow_html=True)
    
    # Setup Section
    uploaded_html = st.file_uploader("Upload Tally Master (Optional)", type=['html', 'htm'])
    ledger_list = ["Suspense A/c", "Cash", "Bank"]
    if uploaded_html:
        extracted = get_ledger_names(uploaded_html)
        if extracted:
            ledger_list = extracted
            st.success(f"Loaded {len(ledger_list)} ledgers")
            
    bank_ledger = st.selectbox("Select Bank Ledger", ledger_list, index=0)
    party_ledger = st.selectbox("Select Default Party", ledger_list, index=0)
    st.markdown('</div>', unsafe_allow_html=True) # Close Card

with col_right:
    st.markdown('<div class="card"><div class="card-header">📂 2. Data Processing</div>', unsafe_allow_html=True)
    
    # File Processing Section
    col_a, col_b = st.columns(2)
    with col_a:
        bank_choice = st.selectbox("Select Bank Format", ["SBI", "PNB", "ICICI", "Axis Bank", "HDFC Bank", "Kotak Mahindra", "Yes Bank", "Other"])
    with col_b:
        pdf_password = st.text_input("PDF Password (if any)", type="password")

    uploaded_file = st.file_uploader("Upload Statement (Excel or PDF)", type=['xlsx', 'xls', 'pdf'])
    
    if uploaded_file:
        df_raw = load_bank_file(uploaded_file, pdf_password)
        
        if df_raw is not None:
            df_clean = normalize_bank_data(df_raw, bank_choice)
            st.dataframe(df_clean.head(), use_container_width=True, hide_index=True)
            
            st.write("")
            if st.button("🚀 Convert to Tally XML"):
                xml_data = generate_tally_xml(df_clean, bank_ledger, party_ledger)
                st.success("Conversion Successful!")
                st.download_button("⬇️ Download XML File", xml_data, "tally_import.xml", "application/xml")
        else:
            st.error("Could not read file. Please check format or password.")
            
    st.markdown('</div>', unsafe_allow_html=True) # Close Card

# --- 6. FOOTER ---
# Logo Logic
try:
    img_b64 = get_img_as_base64("logo 1.png")
    if not img_b64: img_b64 = get_img_as_base64("logo.png")
except: img_b64 = None

logo_html = f'<img src="data:image/png;base64,{img_b64}" width="20" style="vertical-align: middle; margin-right: 5px;">' if img_b64 else ""

st.markdown(f"""
    <div class="footer">
        <p>Sponsored By {logo_html} <a href="#" class="brand-link">Uday Mondal</a> | Consultant Advocate</p>
        <p style="font-size: 12px; margin-top: 5px;">Powered & Created by <span class="brand-link">Debasish Biswas</span></p>
    </div>
""", unsafe_allow_html=True)
