import streamlit as st
import pandas as pd
from bs4 import BeautifulSoup
import datetime
import io

# --- 1. CONFIGURATION & SETUP ---
st.set_page_config(page_title="Tally XML Converter", layout="wide")

st.title("Excel to Tally XML Converter")
st.markdown("Convert Bank Statements (SBI, PNB, ICICI, Axis, HDFC, etc.) to Tally Importable XML.")

# --- 2. HELPER FUNCTIONS ---

def get_ledger_names(html_file):
    """Parses Tally HTML Master export to get ledger names."""
    try:
        soup = BeautifulSoup(html_file, 'html.parser')
        # Tally exports usually have data in table rows <tr> or specific div structures.
        # This is a generic scraper for the default Tally 'List of Accounts' HTML export.
        ledgers = []
        rows = soup.find_all('tr')
        for row in rows:
            cols = row.find_all('td')
            # Usually the first column contains the ledger name in Tally HTML exports
            if cols:
                text = cols[0].get_text(strip=True)
                if text:
                    ledgers.append(text)
        
        # If standard parsing fails (empty list), try a fallback for different Tally versions
        if not ledgers:
            all_text = soup.get_text(separator='\n')
            lines = [line.strip() for line in all_text.split('\n') if line.strip()]
            ledgers = sorted(list(set(lines))) # Basic fallback

        return sorted(ledgers)
    except Exception as e:
        st.error(f"Error parsing HTML: {e}")
        return []

def clean_currency(value):
    """Removes commas and converts to float."""
    if pd.isna(value) or value == '':
        return 0.0
    val_str = str(value).replace(',', '').strip()
    try:
        return float(val_str)
    except ValueError:
        return 0.0

def load_bank_excel(file):
    """
    Smart Loader: Scans the first 30 rows to find the actual header row
    (containing 'Date') to skip logos and address info at the top.
    """
    try:
        # Read first 30 rows without header
        df_temp = pd.read_excel(file, header=None, nrows=30)
        
        header_idx = 0
        found = False
        
        for i, row in df_temp.iterrows():
            row_str = row.astype(str).str.lower().values
            # Look for a row that contains 'date' AND ('balance' OR 'debit' OR 'withdrawal')
            if any('date' in x for x in row_str) and \
               (any('balance' in x for x in row_str) or any('debit' in x for x in row_str) or any('withdrawal' in x for x in row_str)):
                header_idx = i
                found = True
                break
        
        # Reload with the correct header row
        if found:
            file.seek(0) # Reset file pointer
            return pd.read_excel(file, header=header_idx)
        else:
            file.seek(0)
            return pd.read_excel(file)
            
    except Exception as e:
        return None

def normalize_bank_data(df, bank_name):
    """Maps various bank column names to standard: Date, Narration, Debit, Credit"""
    target_columns = ['Date', 'Narration', 'Debit', 'Credit']
    
    # Mapping Dictionary
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
        
        # 1. Rename Columns
        df = df.rename(columns=mapping)
        
        # 2. Ensure target columns exist
        for col in target_columns:
            if col not in df.columns:
                df[col] = 0 if col in ['Debit', 'Credit'] else ""

        # 3. Clean Data
        df['Debit'] = df['Debit'].apply(clean_currency)
        df['Credit'] = df['Credit'].apply(clean_currency)
        df['Narration'] = df['Narration'].fillna('')
        
        # 4. Handle Dates (Attempt to standardize to YYYYMMDD)
        # Note: Tally XML requires YYYYMMDD format
        
        return df[target_columns]
    
    return df # Return as is for "Other"

def generate_tally_xml(df, bank_ledger_name, default_party_ledger):
    """Generates the Tally XML string from the dataframe."""
    xml_header = """<ENVELOPE>
    <HEADER>
    <TALLYREQUEST>Import Data</TALLYREQUEST>
    </HEADER>
    <BODY>
    <IMPORTDATA>
    <REQUESTDESC>
    <REPORTNAME>Vouchers</REPORTNAME>
    </REQUESTDESC>
    <REQUESTDATA>"""
    
    xml_footer = """</REQUESTDATA>
    </IMPORTDATA>
    </BODY>
    </ENVELOPE>"""
    
    xml_body = ""
    
    for index, row in df.iterrows():
        # Determine Voucher Type
        debit_amt = row['Debit']
        credit_amt = row['Credit']
        
        if debit_amt > 0:
            vch_type = "Payment"
            amount = debit_amt
            # For Payment: Party is DEBITED, Bank is CREDITED
            # Ledger 1 (Debit): Party Ledger
            led_1_name = default_party_ledger
            led_1_amt = -amount # Tally Debit is negative in XML context often, but let's stick to standard Positive numbers with IsDeemedPositive tag
            led_1_is_deemed_positive = "Yes"
            
            # Ledger 2 (Credit): Bank Ledger
            led_2_name = bank_ledger_name
            led_2_amt = amount
            led_2_is_deemed_positive = "No"
            
        elif credit_amt > 0:
            vch_type = "Receipt"
            amount = credit_amt
            # For Receipt: Bank is DEBITED, Party is CREDITED
            # Ledger 1 (Debit): Bank Ledger
            led_1_name = bank_ledger_name
            led_1_amt = -amount
            led_1_is_deemed_positive = "Yes"
            
            # Ledger 2 (Credit): Party Ledger
            led_2_name = default_party_ledger
            led_2_amt = amount
            led_2_is_deemed_positive = "No"
        else:
            continue # Skip rows with 0 transaction

        # Format Date to YYYYMMDD
        try:
            date_obj = pd.to_datetime(row['Date'], dayfirst=True) # Assuming DD/MM/YYYY
            date_str = date_obj.strftime("%Y%m%d")
        except:
            date_str = "20240401" # Fallback
            
        # Escape special characters in Narration
        narration = str(row['Narration']).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

        # Construct XML for one voucher
        xml_body += f"""
        <TALLYMESSAGE xmlns:UDF="TallyUDF">
         <VOUCHER VCHTYPE="{vch_type}" ACTION="Create" OBJVIEW="Accounting Voucher View">
          <DATE>{date_str}</DATE>
          <NARRATION>{narration}</NARRATION>
          <VOUCHERTYPENAME>{vch_type}</VOUCHERTYPENAME>
          <ALLLEDGERENTRIES.LIST>
           <LEDGERNAME>{led_1_name}</LEDGERNAME>
           <ISDEEMEDPOSITIVE>{led_1_is_deemed_positive}</ISDEEMEDPOSITIVE>
           <AMOUNT>{led_1_amt}</AMOUNT>
          </ALLLEDGERENTRIES.LIST>
          <ALLLEDGERENTRIES.LIST>
           <LEDGERNAME>{led_2_name}</LEDGERNAME>
           <ISDEEMEDPOSITIVE>{led_2_is_deemed_positive}</ISDEEMEDPOSITIVE>
           <AMOUNT>{led_2_amt}</AMOUNT>
          </ALLLEDGERENTRIES.LIST>
         </VOUCHER>
        </TALLYMESSAGE>"""

    return xml_header + xml_body + xml_footer

# --- 3. STREAMLIT UI ---

# Step 1: Master Upload
st.header("1. Upload Tally Master (Optional)")
st.info("Upload 'List of Accounts.html' exported from Tally to auto-fill Ledger names.")
uploaded_html = st.file_uploader("Upload HTML Master", type=['html', 'htm'])

ledger_list = ["Suspense A/c", "Cash", "Bank"] # Defaults
if uploaded_html is not None:
    extracted_ledgers = get_ledger_names(uploaded_html)
    if extracted_ledgers:
        ledger_list = extracted_ledgers
        st.success(f"Loaded {len(ledger_list)} ledgers from Master file.")

# Step 2: Settings
st.header("2. Settings")
col1, col2 = st.columns(2)
with col1:
    bank_ledger = st.selectbox("Select Your Bank Ledger", ledger_list, index=0)
with col2:
    party_ledger = st.selectbox("Select Default Party (Suspense)", ledger_list, index=0)

# Step 3: Bank Statement
st.header("3. Bank Statement")
bank_options = ["SBI", "PNB", "ICICI", "Axis Bank", "HDFC Bank", "Kotak Mahindra", "Yes Bank", "Other"]
bank_choice = st.selectbox("Select Bank Format", bank_options)

uploaded_file = st.file_uploader("Upload Excel Statement", type=['xlsx', 'xls'])

if uploaded_file is not None:
    # Load and Normalize
    df_raw = load_bank_excel(uploaded_file)
    
    if df_raw is not None:
        df_clean = normalize_bank_data(df_raw, bank_choice)
        
        st.subheader("Data Preview")
        st.dataframe(df_clean.head())
        
        # Step 4: Generate
        if st.button("Generate Tally XML"):
            xml_data = generate_tally_xml(df_clean, bank_ledger, party_ledger)
            
            st.success("XML Generated Successfully!")
            st.download_button(
                label="Download XML File",
                data=xml_data,
                file_name="tally_import.xml",
                mime="application/xml"
            )
    else:
        st.error("Could not read the Excel file. Please ensure it is a valid format.")

