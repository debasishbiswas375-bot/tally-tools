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

# --- 2. FUTURISTIC TALLY THEME CSS ---
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
        
        /* Global Background */
        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif;
            background-color: #F8FAFC; 
            color: #0F172A;
        }

        /* FUTURISTIC HERO SECTION (Tally Green + Tech Blue Gradient) */
        .hero-container {
            text-align: center;
            padding: 50px 20px 50px 20px;
            /* Gradient: Deep Green to Modern Blue */
            background: linear-gradient(135deg, #065F46 0%, #1E40AF 100%);
            color: white;
            margin: -6rem -4rem 30px -4rem; /* Stretch to edges */
            box-shadow: 0 10px 30px -10px rgba(6, 95, 70, 0.5);
            position: relative;
            overflow: hidden;
        }
        
        /* Subtle Tech Grid Pattern Overlay */
        .hero-container::before {
            content: "";
            position: absolute;
            top: 0; left: 0; right: 0; bottom: 0;
            background-image: 
                linear-gradient(rgba(255, 255, 255, 0.1) 1px, transparent 1px), 
                linear-gradient(90deg, rgba(255, 255, 255, 0.1) 1px, transparent 1px);
            background-size: 30px 30px;
            pointer-events: none;
        }

        .hero-title {
            font-size: 3.5rem;
            font-weight: 800;
            margin-top: 10px;
            margin-bottom: 5px;
            text-shadow: 0 4px 10px rgba(0,0,0,0.3);
        }
        
        .hero-subtitle {
            font-size: 1.2rem;
            color: #E2E8F0;
            font-weight: 300;
            opacity: 0.9;
        }

        /* Card Styling (Glass-like White) */
        .stContainer {
            background-color: white;
            padding: 30px;
            border-radius: 16px;
            box-shadow: 0 4px 20px -5px rgba(0, 0, 0, 0.05);
            border: 1px solid #E2E8F0;
        }
        
        /* Headers inside cards (Tally Green Accent) */
        h3 {
            font-size: 1.2rem !important;
            font-weight: 700 !important;
            color: #1e293b !important;
            border-left: 5px solid #10B981; /* Green bar */
            padding-left: 12px;
        }

        /* Buttons (Green/Blue Gradient) */
        .stButton>button {
            width: 100%;
            background: linear-gradient(90deg, #10B981 0%, #3B82F6 100%);
            color: white;
            border-radius: 8px;
            height: 55px;
            font-size: 1rem;
            font-weight: 600;
            border: none;
            box-shadow: 0 4px 15px rgba(16, 185, 129, 0.3);
            transition: all 0.3s ease;
        }
        .stButton>button:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(16, 185, 129, 0.4);
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
        .brand-link {
            color: #059669;
            text-decoration: none;
            font-weight: 700;
        }
        
        /* Hide Default Streamlit Elements */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        
        /* Success Message Box */
        .stAlert {
            background-color: #F0FDF4;
            border: 1px solid #10B981;
            color: #166534;
        }
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

# --- 4. HERO SECTION WITH LOGO ---
# Load logo safely
try:
    img_b64 = get_img_as_base64("logo.png")
except: img_b64 = None

logo_html = f'<img src="data:image/png;base64,{img_b64}" width="120" style="margin-bottom: 20px;">' if img_b64 else ""

st.markdown(f"""
    <div class="hero-container">
        {logo_html}
        <div class="hero-title">Accounting Expert</div>
        <div class="hero-subtitle">Turn messy Bank Statements into Tally Vouchers in seconds.<br>Supports Excel & PDF. 99% Accuracy.</div>
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
                if st.button("🚀 Convert to Tally XML"):
                    xml_data = generate_tally_xml(df_clean, bank_ledger, party_ledger)
                    st.balloons()
                    st.success("Conversion Successful! Ready for Import.")
                    st.download_button("⬇️ Download XML File", xml_data, "tally_import.xml", "application/xml")
            else:
                st.error("⚠️ Could not read file. Check format or password.")

# --- 6. FOOTER ---
# Mini logo for footer
mini_logo_html = f'<img src="data:image/png;base64,{img_b64}" width="20" style="vertical-align: middle; margin-right: 8px;">' if img_b64 else ""

st.markdown(f"""
    <div class="footer">
        <p>Sponsored By {mini_logo_html} <span class="brand-link" style="color:#0F172A;">Uday Mondal</span> | Consultant Advocate</p>
        <p style="font-size: 13px; margin-top: 8px;">Powered & Created by <span class="brand-link">Debasish Biswas</span> | Professional Tally Automation</p>
    </div>
""", unsafe_allow_html=True)


