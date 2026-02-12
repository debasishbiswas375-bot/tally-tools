import streamlit as st
import pandas as pd
from bs4 import BeautifulSoup
import pdfplumber
import re

# --- 1. PAGE CONFIGS ---
st.set_page_config(page_title="Accounting Expert", layout="wide")

# --- 2. LOGIC FIXES ---

def clean_currency(value):
    if pd.isna(value) or value == '': return 0.0
    # Removes commas, currency symbols, and Tally Cr/Dr markers
    val = re.sub(r'[^\d.]', '', str(value))
    try: return float(val)
    except: return 0.0

def trace_ledger(narration, master_ledgers):
    if not narration or not master_ledgers: return None
    # Reverse length match to find 'Mithu Mondal' before 'Mithu'
    sorted_masters = sorted([str(m) for m in master_ledgers], key=len, reverse=True)
    for ledger in sorted_masters:
        if len(ledger) < 3: continue
        if re.search(r'\b' + re.escape(ledger) + r'\b', str(narration), re.IGNORECASE):
            return ledger
    return None

def smart_normalize(df):
    """Fixes the AttributeError by ensuring columns exist before processing."""
    if df.empty: return pd.DataFrame(columns=['Date', 'Narration', 'Debit', 'Credit'])
    
    df = df.dropna(how='all').reset_index(drop=True)
    
    # Locate Header Row
    header_idx = None
    for i, row in df.iterrows():
        row_str = " ".join(row.astype(str).lower())
        if 'date' in row_str and ('narration' in row_str or 'particular' in row_str or 'description' in row_str):
            header_idx = i
            break
    
    if header_idx is not None:
        df.columns = df.iloc[header_idx]
        df = df[header_idx + 1:].reset_index(drop=True)
    
    df.columns = df.columns.astype(str).str.strip().str.lower()

    # Dynamic Column Mapping
    new_df = pd.DataFrame()
    col_map = {
        'Date': ['date', 'txn', 'value'],
        'Narration': ['narration', 'description', 'particulars', 'remarks', 'details'],
        'Debit': ['debit', 'withdrawal', 'out', 'dr'],
        'Credit': ['credit', 'deposit', 'in', 'cr']
    }

    for target, aliases in col_map.items():
        found_col = None
        for col in df.columns:
            if any(alias in col for alias in aliases):
                found_col = col
                break
        if found_col:
            new_df[target] = df[found_col]
        else:
            new_df[target] = 0.0 if target in ['Debit', 'Credit'] else ""

    # Final Cleanup
    new_df['Debit'] = new_df['Debit'].apply(clean_currency)
    new_df['Credit'] = new_df['Credit'].apply(clean_currency)
    return new_df.dropna(subset=['Date'])

def generate_tally_xml(df, bank_ledger):
    """Strictly balanced XML to prevent Tally import errors."""
    xml_header = """<ENVELOPE><HEADER><TALLYREQUEST>Import Data</TALLYREQUEST></HEADER><BODY><IMPORTDATA><REQUESTDESC><REPORTNAME>Vouchers</REPORTNAME></REQUESTDESC><REQUESTDATA>"""
    xml_footer = """</REQUESTDATA></IMPORTDATA></BODY></ENVELOPE>"""
    body = ""
    
    for _, row in df.iterrows():
        amt = row['Debit'] if row['Debit'] > 0 else row['Credit']
        if amt <= 0: continue
        
        vch_type = "Payment" if row['Debit'] > 0 else "Receipt"
        # Tally formatting: Dr is Positive, Cr is Negative
        # For Payment: Party Dr (Positive), Bank Cr (Negative)
        # For Receipt: Bank Dr (Positive), Party Cr (Negative)
        if vch_type == "Payment":
            l1, l1_amt = row['Final Ledger'], amt
            l2, l2_amt = bank_ledger, -amt
        else:
            l1, l1_amt = bank_ledger, amt
            l2, l2_amt = row['Final Ledger'], -amt

        try: d = pd.to_datetime(row['Date'], dayfirst=True).strftime("%Y%m%d")
        except: d = "20260401"
        
        nar = str(row['Narration']).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        
        body += f"""
        <TALLYMESSAGE xmlns:UDF="TallyUDF">
         <VOUCHER VCHTYPE="{vch_type}" ACTION="Create">
          <DATE>{d}</DATE>
          <NARRATION>{nar}</NARRATION>
          <VOUCHERTYPENAME>{vch_type}</VOUCHERTYPENAME>
          <ALLLEDGERENTRIES.LIST>
           <LEDGERNAME>{l1}</LEDGERNAME>
           <ISDEEMEDPOSITIVE>{"Yes" if l1_amt > 0 else "No"}</ISDEEMEDPOSITIVE>
           <AMOUNT>{-l1_amt}</AMOUNT>
          </ALLLEDGERENTRIES.LIST>
          <ALLLEDGERENTRIES.LIST>
           <LEDGERNAME>{l2}</LEDGERNAME>
           <ISDEEMEDPOSITIVE>{"Yes" if l2_amt > 0 else "No"}</ISDEEMEDPOSITIVE>
           <AMOUNT>{-l2_amt}</AMOUNT>
          </ALLLEDGERENTRIES.LIST>
         </VOUCHER>
        </TALLYMESSAGE>"""
        
    return xml_header + body + xml_footer

# --- 3. UI ---
st.title("Accounting Expert | Fixed")

c1, c2 = st.columns([1, 2])

with c1:
    st.header("1. Config")
    master = st.file_uploader("Upload Master.html", type=['html'])
    ledgers = ["Suspense A/c"]
    if master:
        soup = BeautifulSoup(master, 'html.parser')
        ledgers = sorted(list(set([t.text.strip() for t in soup.find_all('td') if t.text.strip()])))
    
    bank_led = st.selectbox("Bank Ledger", ledgers)
    part_led = st.selectbox("Default Party", ledgers)

with c2:
    st.header("2. Process")
    stmt = st.file_uploader("Upload Statement", type=['pdf', 'xlsx'])
    
    if stmt:
        if stmt.name.endswith('.pdf'):
            with pdfplumber.open(stmt) as pdf:
                data = []
                for p in pdf.pages: data.extend(p.extract_table() or [])
            df_raw = pd.DataFrame(data)
        else:
            df_raw = pd.read_excel(stmt)

        if not df_raw.empty:
            df_clean = smart_normalize(df_raw)
            if not df_clean.empty:
                df_clean['Final Ledger'] = df_clean['Narration'].apply(lambda x: trace_ledger(x, ledgers) or part_led)
                
                st.dataframe(df_clean[['Date', 'Narration', 'Final Ledger', 'Debit', 'Credit']])
                
                if st.button("🚀 Generate XML"):
                    xml = generate_tally_xml(df_clean, bank_led)
                    st.download_button("Download XML", xml, "tally.xml")
            else:
                st.error("Could not find table headers in this file. Try a different format.")
