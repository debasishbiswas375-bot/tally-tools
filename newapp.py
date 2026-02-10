import streamlit as st
import pandas as pd
from PIL import Image
from bs4 import BeautifulSoup
import pdfplumber
import io

# --- 1. CONFIGURATION & STYLING ---
st.set_page_config(
    page_title="Accounting Expert",
    page_icon="logo.png",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600&display=swap');
        html, body, [class*="css"] { font-family: 'Poppins', sans-serif; }
        
        /* Main Brand Color: #2E86C1 */
        .brand-text { color: #2E86C1 !important; font-weight: 600; }
        
        .main-header { color: #2E86C1; font-weight: 600; font-size: 2.5rem; margin-bottom: 0px; line-height: 1.2;}
        .sub-header { color: #566573; font-size: 1.1rem; margin-bottom: 30px; }
        .step-container { background-color: #f8f9fa; padding: 20px; border-radius: 10px; border: 1px solid #e9ecef; margin-bottom: 20px; }
        .stButton>button { width: 100%; background-color: #2E86C1; color: white; border-radius: 8px; height: 50px; font-weight: 600; }
        .stButton>button:hover { background-color: #1B4F72; border-color: #1B4F72; }
        .footer { position: fixed; left: 0; bottom: 0; width: 100%; background-color: #ffffff; color: #555; text-align: center; padding: 10px; border-top: 1px solid #eee; z-index: 1000; font-size: 14px; }
        #MainMenu { visibility: hidden; } footer { visibility: hidden; }
        
        /* Sidebar Title Override */
        [data-testid="stSidebarNav"] + div h1 { color: #2E86C1; }
    </style>
""", unsafe_allow_html=True)

# --- 2. LOGIC FUNCTIONS ---

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

# --- PDF EXTRACTION ---
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
        
        header_idx = 0
        found_header = False
        for i, row in df.iterrows():
            row_str = row.astype(str).str.lower().values
            if any('date' in x for x in row_str) and \
               (any('balance' in x for x in row_str) or any('debit' in x for x in row_str) or any('withdrawal' in x for x in row_str)):
                header_idx = i
                found_header = True
                break
        
        if found_header:
            new_header = df.iloc[header_idx]
            df = df[header_idx + 1:] 
            df.columns = new_header
        return df

    except Exception as e:
        if "Password" in str(e):
            st.error("🔒 Incorrect Password!")
        else:
            st.error(f"Error processing PDF: {e}")
        return None

def load_bank_file(file, password=None):
    filename = file.name.lower()
    if filename.endswith('.pdf'):
        return extract_data_from_pdf(file, password)
    else: 
        try:
            df_temp = pd.read_excel(file, header=None, nrows=30)
            header_idx = 0
            found = False
            for i, row in df_temp.iterrows():
                row_str = row.astype(str).str.lower().values
                
                # Check for key columns
                has_date = any('date' in x for x in row_str)
                has_amt = (any('balance' in x for x in row_str) or any('debit' in x for x in row_str))
                
                if has_date and has_amt:
                    header_idx = i
                    found = True
                    break
            
            if found:
                file.seek(0)
                # Safely split into multiple lines to prevent copy errors
                return pd.read_excel(
                    file, 
                    header=header_idx
                )
            return pd.read_excel(file)
        except: return None

def normalize_bank_data(df, bank_name):
    target_columns = ['Date', 'Narration', 'Debit', 'Credit']
    df.columns = df.columns.astype(str).str.replace('\n', ' ').str.strip()
    
    mappings = {
        'SBI': {
            'Txn Date': 'Date', 'Description': 'Narration', 'Debit': 'Debit', 'Credit': 'Credit'
        },
        'PNB': {
            'Transaction Date': 'Date', 'Narration': 'Narration', 'Debit Amount': 'Debit', 'Credit Amount': 'Credit'
        },
        'ICICI': {
            'Value Date': 'Date', 'Transaction Remarks': 'Narration', 
            'Withdrawal Amount (INR )': 'Debit', 'Deposit Amount (INR )': 'Credit'
        },
        'Axis Bank': {
            'Tran Date': 'Date', 'Particulars': 'Narration', 'Debit': 'Debit', 'Credit': 'Credit'
        },
        'HDFC Bank': {
            'Date': 'Date', 'Narration': 'Narration', 'Withdrawal Amt.': 'Debit', 'Deposit Amt.': 'Credit'
        },
        'Kotak Mahindra': {
            'Transaction Date': 'Date', 'Transaction Details': 'Narration', 
            'Withdrawal Amount': 'Debit', 'Deposit Amount': 'Credit'
        },
        'Yes Bank': {
            'Value Date': 'Date', 'Description': 'Narration', 'Debit Amount': 'Debit', 'Credit Amount': 'Credit'
        },
        'Indian Bank': {
            'Value Date': 'Date', 'Narration': 'Narration', 'Debit': 'Debit', 'Credit': 'Credit'
        },
        'India Post (IPPB)': {
            'Date': 'Date', 'Remarks': 'Narration', 'Debit Amount': 'Debit', 'Credit Amount': 'Credit'
        },
        'RBL Bank': {
            'Transaction Date': 'Date', 'Transaction Description': 'Narration', 
            'Withdrawal Amount': 'Debit', 'Deposit Amount': 'Credit'
        }
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

        # --- SAFE XML GENERATION ---
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

# --- 3. UI LAYOUT ---
with st.sidebar:
    try:
        sidebar_logo = Image.open('logo.png')
        st.image(sidebar_logo, width=60)
    except: pass
    
    st.markdown('<h1 class="brand-text" style="font-size: 2rem;">Tally Tools</h1>', unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("### 📝 Instructions")
    st.markdown("""
    1. **Upload Master:** Load 'List of Accounts.html'.
    2. **Settings:** Select Ledgers.
    3. **Upload File:** Excel OR PDF statement.
    4. **Generate:** Download XML.
    """)
    st.info("💡 Supports: Excel & PDF (SBI, HDFC, ICICI, IPPB, RBL, etc.)")

# Header
header_container = st.container()
with header_container:
    col_img, col_txt = st.columns([0.5, 5])
    with col_img:
        try:
            logo_img = Image.open('logo.png')
            st.image(logo_img, use_container_width=True)
        except: st.markdown("## 📊")
    with col_txt:
        st.markdown('<p class="main-header" style="margin-top: 10px;">Accounting Expert</p>', unsafe_allow_html=True)
        st.markdown('<p class="sub-header">Excel & PDF to Tally XML Converter</p>', unsafe_allow_html=True)

st.divider()

# Setup
with st.container(border=True):
    st.markdown("### 🛠️ Step 1: Configuration")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**1. Upload Master (Optional)**")
        uploaded_html = st.file_uploader("Upload 'List of Accounts.html'", type=['html', 'htm'])
        ledger_list = ["Suspense A/c", "Cash", "Bank"]
        if uploaded_html:
            extracted = get_ledger_names(uploaded_html)
            if extracted:
                ledger_list = extracted
                st.success(f"✅ Loaded {len(ledger_list)} ledgers")
    with col2:
        st.markdown("**2. Ledger Mapping**")
        bank_ledger = st.selectbox("Select Bank Ledger", ledger_list, index=0)
        party_ledger = st.selectbox("Select Default Party", ledger_list, index=0)

# Processing
with st.container(border=True):
    st.markdown("### 📂 Step 2: Bank Statement")
    
    col3, col4 = st.columns([1, 2])
    with col3:
        bank_options = ["SBI", "PNB", "ICICI", "Axis Bank", "HDFC Bank", "Kotak Mahindra", "Yes Bank", "Indian Bank", "India Post (IPPB)", "RBL Bank", "Other"]
        bank_choice = st.selectbox("Select Bank Format", bank_options)
    
    with col4:
        uploaded_file = st.file_uploader("Upload Statement (Excel or PDF)", type=['xlsx', 'xls', 'pdf'])
        
        pdf_password = None
        if uploaded_file is not None and uploaded_file.name.endswith('.pdf'):
            st.warning("🔒 If PDF is password protected, enter it below:")
            pdf_password = st.text_input("PDF Password", type="password")

    if uploaded_file:
        df_raw = load_bank_file(uploaded_file, password=pdf_password)
        
        if df_raw is not None:
            df_clean = normalize_bank_data(df_raw, bank_choice)
            
            with st.expander("👁️ Preview Processed Data"):
                st.dataframe(df_clean.head(), use_container_width=True)

            st.write("") 
            if st.button("✨ Generate Tally XML ✨"):
                xml_data = generate_tally_xml(df_clean, bank_ledger, party_ledger)
                st.balloons()
                st.success("XML Generated! Download below:")
                st.download_button("Download XML", xml_data, "tally_import.xml", "application/xml")
        else:
            if not pdf_password and uploaded_file.name.endswith('.pdf'):
                st.info("ℹ️ If the PDF is encrypted, please enter the password above.")
            else:
                st.error("❌ Error reading file. Ensure it is a valid Statement format.")

# Footer
st.markdown("""
    <div class="footer">
        <p style="font-size: 15px; margin-top: 5px;">Sponsored By <b class="brand-text">Uday Mondal</b> | Consultant Advocate</p>
        <p>Powered & Created by <b class="brand-text">Debasish Biswas</b> | Professional Tally Automation</p>
    </div>
""", unsafe_allow_html=True)
