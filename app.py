import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Tally XML Converter", layout="centered")

st.title("📊 Excel to Tally XML Converter")
st.write("Upload your **Transactions.xls** file below to generate your XML import file.")

# File Uploader
uploaded_file = st.file_uploader("Choose an Excel file", type=["xls", "xlsx"])

if uploaded_file:
    try:
        # Load the sheet
        df = pd.read_excel(uploaded_file, sheet_name='Sheet1')
        
        # Filter rows where Date (Index 5) is a number (YYYYMMDD)
        vouchers = df[df.iloc[:, 5].astype(str).str.match(r'^\d{8}(\.0)?$')].copy()
        
        st.info(f"Detected {len(vouchers)} valid transaction rows.")

        xml_lines = [
            '<ENVELOPE>',
            '  <HEADER><TALLYREQUEST>Import Data</TALLYREQUEST></HEADER>',
            '  <BODY><IMPORTDATA><REQUESTDESC><REPORTNAME>Vouchers</REPORTNAME>',
            '  <STATICVARIABLES><SVCURRENTCOMPANY/></STATICVARIABLES></REQUESTDESC><REQUESTDATA>'
        ]

        for _, row in vouchers.iterrows():
            # (Your logic for cleaning data remains the same)
            vch_date = str(int(float(row.iloc[5])))
            vch_type = str(row.iloc[7])
            guid = str(row.iloc[10])
            # ... [Rest of your XML construction logic from tally.py] ...
            
            # Placeholder for your specific XML structure
            msg = f'        <TALLYMESSAGE xmlns:UDF="TallyUDF">...</TALLYMESSAGE>'
            xml_lines.append(msg)

        xml_lines.extend(['</REQUESTDATA></IMPORTDATA></BODY></ENVELOPE>'])
        final_xml = "\n".join(xml_lines)

        # Download Button
        st.download_button(
            label="📥 Download Final_Fixed_Import.xml",
            data=final_xml,
            file_name="Final_Fixed_Import.xml",
            mime="application/xml"
        )
    except Exception as e:
        st.error(f"Error processing file: {e}")