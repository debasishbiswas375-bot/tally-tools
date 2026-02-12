import streamlit as st
import pandas as pd
from bs4 import BeautifulSoup
import pdfplumber
import io
import base64
import re

# --- 1. PAGE CONFIG & THEME ---
st.set_page_config(page_title="Accounting Expert", layout="wide")
st.markdown("""
    <style>
        .stButton>button { width: 100%; background: #10B981; color: white; height: 50px; font-weight: 700; border-radius: 10px; }
        .hero { text-align: center; padding: 40px; background: linear-gradient(135deg, #065F46 0%, #1E40AF 100%); color: white; margin: -6rem -4rem 2rem -4rem; }
        .info-box { background-color: #E0F2FE; border: 1px solid #3B82F6; padding: 10px; border-radius: 8px; margin-bottom: 20px; }
    </style>
""", unsafe_allow_html=True)

# --- 2. CORE ENGINES ---
def extract_masters(html_file):
    soup = BeautifulSoup(html_file, 'html.parser')
    return sorted(list(set([td.text.strip() for td in soup.find_all('td') if len(td.text.strip()) > 1])), key=len, reverse=True)

def clean_bob_pdf(file):
    """Deep Scan for BOB PDF Header Structure"""
    with pdfplumber.open(file) as pdf:
        all_rows = []
        for page in pdf.pages:
            table = page.extract_table()
            if table:
                all_rows.extend(table)
    
    if not all_rows: return None
    
    # Clean the messy BOB headers
    df = pd.DataFrame(all_rows)
    # Find the row where the actual data starts (usually after headers like 'DR/CR')
    data_start = 0
    for i, row in df.iterrows():
        row_str = " ".join([str(x) for x in row if x]).upper()
        if 'CR/DR' in row_str or 'DESCRIPTION' in row_str:
            data_start = i + 1
            break
            
    # Clean newlines and spaces from columns
    final_df = df[data_start:].reset_index(drop=True)
    return final_df

def generate_safe_xml(df, bank_led, masters, upi_fix="Suspense"):
    header = '<?xml version="1.0" encoding="UTF-8"?><ENVELOPE><HEADER><TALLYREQUEST>Import Data</TALLYREQUEST></HEADER><BODY><IMPORTDATA><REQUESTDESC><REPORTNAME>Vouchers</REPORTNAME><STATICVARIABLES><SVCURRENTCOMPANY/></STATICVARIABLES></REQUESTDESC><REQUESTDATA>'
    footer = '</REQUESTDATA></IMPORTDATA></BODY></ENVELOPE>'
    body = ""
    
    for _, row in df.iterrows():
        try:
            # Your PDF has Description in column 4 and CR/DR in column 5
            nar = str(row.iloc[4]).replace('\n', ' ').replace('&', '&amp;').replace('<', '&lt;')
            dt_raw = str(row.iloc[2]).split(' ')[0]
            dt = pd.to_datetime(dt_raw, dayfirst=True).strftime('%Y%m%d')
            
            mode = str(row.iloc[5]).strip().upper()
            amt = float(str(row.iloc[6]).replace(',', ''))
            
            # Identity Trace
            target = "Suspense"
            for m in masters:
                if re.search(rf"\b{re.escape(m.upper())}\b", nar.upper()):
                    target = m
                    break
            if target == "Suspense" and "UPI" in nar.upper(): target = upi_fix

            # Debit/Credit Mapping
            l1, l1_amt = (target, -amt) if 'DR' in mode else (bank_led, -amt)
            l2, l2_amt = (bank_led, amt) if 'DR' in mode else (target, amt)
            vtype = "Payment" if 'DR' in mode else "Receipt"
            
            body += f'<TALLYMESSAGE xmlns:UDF="TallyUDF"><VOUCHER VCHTYPE="{vtype}" ACTION="Create"><DATE>{dt}</DATE><NARRATION>{nar}</NARRATION><VOUCHERTYPENAME>{vtype}</VOUCHERTYPENAME><ALLLEDGERENTRIES.LIST><LEDGERNAME>{l1}</LEDGERNAME><ISDEEMEDPOSITIVE>{"Yes" if l1_amt < 0 else "No"}</ISDEEMEDPOSITIVE><AMOUNT>{l1_amt}</AMOUNT></ALLLEDGERENTRIES.LIST><ALLLEDGERENTRIES.LIST><LEDGERNAME>{l2}</LEDGERNAME><ISDEEMEDPOSITIVE>{"Yes" if l2_amt < 0 else "No"}</ISDEEMEDPOSITIVE><AMOUNT>{l2_amt}</AMOUNT></ALLLEDGERENTRIES.LIST></VOUCHER></TALLYMESSAGE>'
        except: continue
    return header + body + footer

# --- 3. UI DASHBOARD ---
st.markdown('<div class="hero"><h1>Accounting Expert</h1></div>', unsafe_allow_html=True)

c1, c2 = st.columns([1, 1.2])
with c1:
    m_file = st.file_uploader("Upload Master.html", type=['html'])
    masters = extract_masters(m_file) if m_file else []
    bank_led = st.selectbox("Select Bank Ledger", ["⭐ Auto-Detect"] + masters)

with c2:
    s_file = st.file_uploader("Upload Statement", type=['xlsx', 'xls', 'pdf'])
    if s_file and m_file:
        # Specialized cleaning for your PDF
        df = clean_bob_pdf(s_file) if s_file.name.endswith('.pdf') else pd.read_excel(s_file)
        
        if df is not None:
            # Auto-Detect BOB 0138 from PDF text
            if bank_led == "⭐ Auto-Detect":
                if "090205014386" in str(df.values) or "0138" in str(df.values):
                    bank_led = next((m for m in masters if "0138" in m), "BOB A/C NO- 0138")
            
            st.markdown(f'<div class="info-box">🏦 <b>Active Bank:</b> {bank_led}</div>', unsafe_allow_html=True)
            
            if st.button("🚀 Process & Generate Tally XML"):
                xml_data = generate_safe_xml(df, bank_led, masters)
                if len(xml_data) > 500:
                    st.success("✅ Tally Prime XML Generated!")
                    st.download_button("⬇️ Download XML", xml_data, "tally_import.xml")
                else:
                    st.error("No valid transactions found in PDF.")
