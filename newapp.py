import streamlit as st
import pandas as pd
from PIL import Image
from bs4 import BeautifulSoup
import io

# --- 1. CONFIGURATION & SETUP ---
st.set_page_config(
    page_title="Accounting Expert",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. CUSTOM CSS (Styling) ---
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600&display=swap');
        html, body, [class*="css"] {
            font-family: 'Poppins', sans-serif;
        }
        .main-header {
            color: #1E3A8A;
            font-weight: 700;
            font-size: 2.5rem;
            margin-bottom: 10px;
        }
        .sub-header {
            color: #555;
            font-size: 1.1rem;
            margin-bottom: 20px;
        }
        /* Hide default Streamlit menu */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- 3. HELPER FUNCTIONS ---

def get_ledger_names(html_file):
    try:
        soup = BeautifulSoup(html_file, 'html.parser')
        ledgers = []
        rows = soup.find_all('tr')
        for row in rows:
            cols = row.find_all('td')
            if cols:
                text = cols[0].get_text(strip=True)
                if text:
                    ledgers.append(text)
        if not ledgers:
            all_text = soup.get_text(separator='\n')
            lines = [line.strip() for line in all_text.split('\n') if line.strip()]
            ledgers = sorted(list(set(lines)))
        return sorted(ledgers)
    except Exception:
        return []

def clean_currency(value):
    if pd.isna(value) or value == '':
        return 0.0
    val_str = str(value).replace(',', '').strip()
    try:
        return float(val_str)
    except ValueError:
        return 0.0

def load_bank_excel(file):
    try:
        df_temp = pd.read_excel(file, header=None, nrows=30)
        header_idx = 0
        found = False
        for i, row in df_temp.iterrows():
            row_str = row.astype(str).str.lower().values
            if any('date' in x for x in row_str) and \
               (any('balance' in x for x in row_str) or any('debit' in x for x in row_str) or any('withdrawal' in x for x in row_str)):
                header_idx = i
                found = True
                break
        if found:
            file.seek(0)
            return pd.read_excel(file, header=header_idx)
        else:
            file.seek(0)
            return pd.read_excel(file)
    except Exception:
        return None

def normalize_bank_data(df, bank_name):
    target_columns = ['Date', 'Narration', 'Debit', 'Credit']
    mappings = {
        'SBI': {'Txn Date': 'Date', 'Description': 'Narration', 'Debit': 'Debit', 'Credit': 'Credit'},
        'PNB': {'Transaction Date': 'Date', 'Narration': 'Narration', 'Debit Amount': 'Debit', 'Credit Amount': 'Credit'},
        'ICICI': {'Value Date': 'Date', 'Transaction Remarks': 'Narration', 'Withdrawal Amount (INR )': 'Debit', 'Deposit Amount (INR )': 'Credit'},
        'Axis Bank': {'Tran Date': 'Date', 'Particulars': 'Narration', 'Debit': 'Debit', 'Credit': 'Credit'},
        'HDFC Bank': {'Date': 'Date', 'Narration': 'Narration', 'Withdrawal Amt.': 'Debit', 'Deposit Amt.': 'Credit'},
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
            led_1_name, led_1_amt, led_1_pos = default_party_ledger, -amount, "Yes"
            led_2_name, led_2_amt, led_2_pos = bank_ledger_name, amount, "No"
        elif credit_amt > 0:
            vch_type = "Receipt"
            amount = credit_amt
            led_1_name, led_1_amt, led_1_pos = bank_ledger_name, -amount, "Yes"
            led_2_name, led_2_amt, led_2_pos = default_party_ledger, amount, "No"
        else:
            continue

        try:
            date_obj = pd.to_datetime(row['Date'], dayfirst=True)
            date_str = date_obj.strftime("%Y%m%d")
        except:
            date_str = "20240401"
            
        narration = str(row['Narration']).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

        xml_body += f"""
        <TALLYMESSAGE xmlns:UDF="TallyUDF">
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

# --- 4. HEADER WITH LOGO ---
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    try:
        # Tries to find 'logo.png' in the root folder
        image = Image.open('logo.png')
        st.image(image, use_container_width=True)
    except FileNotFoundError:
        st.markdown('<p class="main-header" style="text-align: center;">ACCOUNTING EXPERT</p>', unsafe_allow_html=True)

st.markdown('<p class="sub-header" style="text-align: center;">Bank to Tally XML Converter</p>', unsafe_allow_html=True)
st.divider()

# --- 5. MAIN APPLICATION ---

# Section 1: Settings
with st.container(border=True):
    st.subheader("1. Settings")
    col_a, col_b = st.columns(2)
    
    with col_a:
        uploaded_html = st.file_uploader("Upload Tally Master (HTML)", type=['html', 'htm'])
        ledger_list = ["Suspense A/c", "Cash", "Bank"]
        if uploaded_html:
            extracted = get_ledger_names(uploaded_html)
            if extracted:
                ledger_list = extracted
                st.success(f"✅ Loaded {len(ledger_list)} ledgers")

    with col_b:
        bank_ledger = st.selectbox("Select Bank Ledger", ledger_list, index=0)
        party_ledger = st.selectbox("Select Default Party", ledger_list, index=0)

# Section 2: File Processing
with st.container(border=True):
    st.subheader("2. Bank Statement")
    
    col_c, col_d = st.columns([1, 2])
    with col_c:
        bank_options = ["SBI", "PNB", "ICICI", "Axis Bank", "HDFC Bank", "Kotak Mahindra", "Yes Bank", "Other"]
        bank_choice = st.selectbox("Select Bank Format", bank_options)
    with col_d:
        uploaded_file = st.file_uploader("Upload Excel Statement", type=['xlsx', 'xls'])

    if uploaded_file:
        df_raw = load_bank_excel(uploaded_file)
        if df_raw is not None:
            df_clean = normalize_bank_data(df_raw, bank_choice)
            
            st.write("Preview:")
            st.dataframe(df_clean.head(), use_container_width=True)

            if st.button("Generate XML", type="primary"):
                xml_data = generate_tally_xml(df_clean, bank_ledger, party_ledger)
                st.success("Success! Download below:")
                st.download_button("Download Tally XML", xml_data, "tally_import.xml", "application/xml")
        else:
            st.error("Error reading file. Please check format.")
