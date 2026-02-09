import streamlit as st
import pandas as pd
from bs4 import BeautifulSoup
import datetime
import io

# --- 1. Helper Functions ---
def load_ledgers_from_html(html_file):
    """Parses master.html to find Tally ledgers."""
    try:
        soup = BeautifulSoup(html_file, 'html.parser')
        ledgers = set()
        # Look for table data or list items which usually contain ledger names
        for tag in soup.find_all(['td', 'li']):
            text = tag.get_text(strip=True)
            if text and len(text) > 2:  # Basic filter
                ledgers.add(text)
        return sorted(list(ledgers))
    except Exception as e:
        st.error(f"Error parsing HTML: {e}")
        return []

def generate_xml(df, bank_ledger, second_ledger_default):
    """Generates the Tally XML string."""
    xml_output = """<ENVELOPE>\n<HEADER>\n<TALLYREQUEST>Import Data</TALLYREQUEST>\n</HEADER>\n<BODY>\n<IMPORTDATA>\n<REQUESTDESC>\n<REPORTNAME>Vouchers</REPORTNAME>\n<STATICVARIABLES>\n<SVCURRENTCOMPANY>Company Name</SVCURRENTCOMPANY>\n</STATICVARIABLES>\n</REQUESTDESC>\n<REQUESTDATA>"""
    
    for index, row in df.iterrows():
        # Auto-detect Voucher Type if not present
        if 'Voucher Type' not in df.columns:
             # Basic logic: If 'Withdrawal' column exists and > 0, it's Payment
             # This depends on your specific Bank Statement format
             v_type = "Payment" # Placeholder default
        else:
             v_type = row.get('Voucher Type', 'Payment')

        amount = 100 # Placeholder amount, map this to your real column
        narration = row.get('Narration', '')
        date_str = "20250401" # Placeholder date

        # XML Structure (Simplified)
        xml_output += f"""
        <TALLYMESSAGE xmlns:UDF="TallyUDF">
            <VOUCHER VCHTYPE="{v_type}" ACTION="Create">
                <DATE>{date_str}</DATE>
                <NARRATION>{narration}</NARRATION>
                <ALLLEDGERENTRIES.LIST>
                    <LEDGERNAME>{second_ledger_default}</LEDGERNAME>
                    <ISDEEMEDPOSITIVE>Yes</ISDEEMEDPOSITIVE>
                    <AMOUNT>-{amount}</AMOUNT>
                </ALLLEDGERENTRIES.LIST>
                <ALLLEDGERENTRIES.LIST>
                    <LEDGERNAME>{bank_ledger}</LEDGERNAME>
                    <ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE>
                    <AMOUNT>{amount}</AMOUNT>
                </ALLLEDGERENTRIES.LIST>
            </VOUCHER>
        </TALLYMESSAGE>"""

    xml_output += "\n</REQUESTDATA>\n</IMPORTDATA>\n</BODY>\n</ENVELOPE>"
    return xml_output

# --- 2. The Mobile App Layout ---
st.title("📱 Tally Bank Import Tool")

# Step 1: Upload Master File
st.header("1. Upload Master")
uploaded_master = st.file_uploader("Upload 'master.html'", type=['html'])

ledger_options = []
if uploaded_master is not None:
    # Read the file
    stringio = io.StringIO(uploaded_master.getvalue().decode("utf-8"))
    ledger_options = load_ledgers_from_html(stringio)
    st.success(f"Loaded {len(ledger_options)} ledgers!")

# Step 2: Configuration
st.header("2. Settings")
col1, col2 = st.columns(2)

with col1:
    # Financial Year Logic
    current_year = datetime.datetime.now().year
    fy_list = [f"FY {y}-{str(y+1)[-2:]}" for y in range(current_year-3, current_year+2)]
    selected_fy = st.selectbox("Financial Year", fy_list, index=3)

with col2:
    # First Ledger (Bank)
    selected_bank = st.selectbox("Bank Ledger", ledger_options if ledger_options else ["Upload Master First"])

# Second Ledger (Default)
selected_second_ledger = st.selectbox("Second Ledger (Default Party)", ledger_options if ledger_options else ["Upload Master First"])

# Step 3: Upload Bank Statement
st.header("3. Bank Statement")
uploaded_bank_stmt = st.file_uploader("Upload Excel Statement", type=['xlsx', 'xls'])

if uploaded_bank_stmt and st.button("Generate XML"):
    # Process the file
    try:
        df = pd.read_excel(uploaded_bank_stmt)
        st.write("Preview of Statement:", df.head())
        
        # Generate XML
        xml_data = generate_xml(df, selected_bank, selected_second_ledger)
        
        # Download Button
        st.download_button(
            label="⬇️ Download Tally XML",
            data=xml_data,
            file_name="TallyImport.xml",
            mime="application/xml"
        )
    except Exception as e:
        st.error(f"Error processing file: {e}")
