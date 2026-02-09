import pandas as pd
import os

def generate_fixed_tally_xml(input_excel, output_xml):
    if not os.path.exists(input_excel):
        print(f"Error: {input_excel} not found.")
        return

    try:
        # Load the sheet. Based on previous diagnosis, it is named 'Sheet1'
        df = pd.read_excel(input_excel, sheet_name='Sheet1')
    except Exception as e:
        print(f"Error reading Excel: {e}")
        return

    # FIXED: Strict filter to only keep rows where the Date (Index 5) is a number (YYYYMMDD)
    # This automatically skips all header rows containing </DATE>, </VOUCHERTYPENAME>, etc.
    vouchers = df[df.iloc[:, 5].astype(str).str.match(r'^\d{8}(\.0)?$')].copy()
    
    print(f"Detected {len(vouchers)} valid transaction rows.")

    xml_lines = [
        '<ENVELOPE>',
        '  <HEADER><TALLYREQUEST>Import Data</TALLYREQUEST></HEADER>',
        '  <BODY>',
        '    <IMPORTDATA>',
        '      <REQUESTDESC>',
        '        <REPORTNAME>Vouchers</REPORTNAME>',
        '        <STATICVARIABLES><SVCURRENTCOMPANY/></STATICVARIABLES>',
        '      </REQUESTDESC>',
        '      <REQUESTDATA>'
    ]

    for _, row in vouchers.iterrows():
        # Data Extraction and cleaning
        vch_date = str(int(float(row.iloc[5])))
        vch_type = str(row.iloc[7])
        narration = str(row.iloc[9]) if pd.notna(row.iloc[9]) else ""
        guid = str(row.iloc[10])
        alterid = str(int(float(row.iloc[11]))) if pd.notna(row.iloc[11]) and str(row.iloc[11]).replace('.0','').isdigit() else ""
        
        # Ledger Names directly from Transactions.xls
        l1_name = str(row.iloc[15]) 
        l1_amt = str(row.iloc[16]) 
        l1_is_pos = str(row.iloc[14])

        l2_name = str(row.iloc[34])
        l2_amt = str(row.iloc[35])
        l2_is_pos = str(row.iloc[33])

        # Exact nested structure from your working tally.xml
        msg = '        <TALLYMESSAGE xmlns:UDF="TallyUDF">\n'
        msg += f'          <VOUCHER REMOTEID="{guid}" VCHTYPE="{vch_type}" ACTION="Create">\n'
        msg += f'            <DATE>{vch_date}</DATE>\n'
        msg += f'            <EFFECTIVEDATE>{vch_date}</EFFECTIVEDATE>\n'
        msg += f'            <VOUCHERTYPENAME>{vch_type}</VOUCHERTYPENAME>\n'
        msg += f'            <VOUCHERNUMBER>0</VOUCHERNUMBER>\n'
        msg += f'            <NARRATION>{narration}</NARRATION>\n'
        msg += f'            <GUID>{guid}</GUID>\n'
        msg += f'            <ALTERID>{alterid}</ALTERID>\n'
        msg += '            <ALLLEDGERENTRIES.LIST>\n'
        msg += f'              <LEDGERNAME>{l1_name}</LEDGERNAME>\n'
        msg += f'              <ISDEEMEDPOSITIVE>{l1_is_pos}</ISDEEMEDPOSITIVE>\n'
        msg += f'              <AMOUNT>{l1_amt}</AMOUNT>\n'
        msg += '            </ALLLEDGERENTRIES.LIST>\n'
        msg += '            <ALLLEDGERENTRIES.LIST>\n'
        msg += f'              <LEDGERNAME>{l2_name}</LEDGERNAME>\n'
        msg += f'              <ISDEEMEDPOSITIVE>{l2_is_pos}</ISDEEMEDPOSITIVE>\n'
        msg += f'              <AMOUNT>{l2_amt}</AMOUNT>\n'
        msg += '            </ALLLEDGERENTRIES.LIST>\n'
        msg += '          </VOUCHER>\n'
        msg += '        </TALLYMESSAGE>'
        xml_lines.append(msg)

    xml_lines.extend(['      </REQUESTDATA>', '    </IMPORTDATA>', '  </BODY>', '</ENVELOPE>'])

    with open(output_xml, "w", encoding='utf-8') as f:
        f.write("\n".join(xml_lines))
    print(f"Success: Created {output_xml}")

# Ensure the file name is 'Transactions.xls' in your folder
generate_fixed_tally_xml('Transactions.xls', 'Final_Fixed_Import.xml')