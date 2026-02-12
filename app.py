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
    </style>
""", unsafe_allow_html=True)

# --- 2. CORE ENGINES ---
def extract_masters(html_file):
    soup = BeautifulSoup(html_file, 'html.parser')
    return sorted(list(set([td.text.strip() for td in soup.find_all('td') if len(td.text.strip()) > 1])), key=len, reverse=True)

def generate_safe_xml(df, bank_led, masters, upi_fix="Suspense"):
    # Header matching Final_Fixed_Import.xml structure
    header = '<?xml version="1.0" encoding="UTF-8"?><ENVELOPE><HEADER><TALLYREQUEST>Import Data</TALLYREQUEST></HEADER><BODY><IMPORTDATA><REQUESTDESC><REPORTNAME>Vouchers</REPORTNAME><STATICVARIABLES><SVCURRENTCOMPANY/></STATICVARIABLES></REQUESTDESC><REQUESTDATA>'
    footer = '</REQUESTDATA></IMPORTDATA></BODY></ENVELOPE>'
    body = ""
    
    # Identify Columns
    cols = df.columns.tolist()
    nar_idx = next((i for i, c in enumerate(cols) if 'NARRATION' in str(c).upper()), 1)
    dr_idx = next((i for i, c in enumerate(cols) if any(x in str(c).upper() for x in ['WITHDRAWAL', 'DEBIT'])), None)
    cr_idx = next((i for i, c in enumerate(cols) if any(x in str(c).upper() for x in ['DEPOSIT', 'CREDIT'])), None)
    date_idx = 0

    for _, row in df.iterrows():
        try:
            nar = str(row.iloc[nar_idx]).replace('&', '&amp;').replace('<', '&lt;')
            dt = pd.to_datetime(row.iloc[date_idx]).strftime('%Y%m%d')
            dr = float(str(row.iloc[dr_idx]).replace(',', '')) if dr_idx and pd.notna(row.iloc[dr_idx]) else 0
            cr = float(str(row.iloc[cr_idx]).replace(',', '')) if cr_idx and pd.notna(row.iloc[cr_idx]) else 0
            
            # Identity Trace
            target = "Suspense"
            for m in masters:
                if re.search(rf"\b{re.escape(m.upper())}\b", nar.upper()):
                    target = m
                    break
            if target == "Suspense" and "UPI" in nar.upper(): target = upi_fix

            if dr > 0 or cr > 0:
                vtype = "Payment" if dr > 0 else "Receipt"
                amt = dr if dr > 0 else cr
                # Debit/Credit Logic for Tally
                l1, l1_amt = (target, -amt) if dr > 0 else (bank_led, -amt)
                l2, l2_amt = (bank_led, amt) if dr > 0 else (target, amt)
                
                body += f'<TALLYMESSAGE xmlns:UDF="TallyUDF"><VOUCHER VCHTYPE="{vtype}" ACTION="Create"><DATE>{dt}</DATE><NARRATION>{nar}</NARRATION><VOUCHERTYPENAME>{vtype}</VOUCHERTYPENAME><ALLLEDGERENTRIES.LIST><LEDGERNAME>{l1}</LEDGERNAME><ISDEEMEDPOSITIVE>{"Yes" if l1_amt < 0 else "No"}</ISDEEMEDPOSITIVE><AMOUNT>{l1_amt}</AMOUNT></ALLLEDGERENTRIES.LIST><ALLLEDGERENTRIES.LIST><LEDGERNAME>{l2}</LEDGERNAME><ISDEEMEDPOSITIVE>{"Yes" if l2_amt < 0 else "No"}</ISDEEMEDPOSITIVE><AMOUNT>{l2_amt}</AMOUNT></ALLLEDGERENTRIES.LIST></VOUCHER></TALLYMESSAGE>'
        except: continue
    return header + body + footer

# --- 3. UI ---
st.markdown('<div class="hero"><h1>Accounting Expert</h1></div>', unsafe_allow_html=True)

col1, col2 = st.columns(2)
with col1:
    m_file = st.file_uploader("Upload Master.html", type=['html'])
    masters = extract_masters(m_file) if m_file else []
    bank_led = st.selectbox("Select Bank Account", ["⭐ Auto-Detect"] + masters)

with col2:
    s_file = st.file_uploader("Upload Statement", type=['xlsx', 'xls', 'pdf'])
    if s_file and m_file:
        df = pd.read_excel(s_file) if not s_file.name.endswith('.pdf') else pd.DataFrame() # Simplified for Excel
        
        # --- AUTO-DETECT BANK ACCOUNT ---
        # Scans the top of your Excel file for '0138'
        if bank_led == "⭐ Auto-Detect":
            statement_text = str(df.iloc[:5].values).upper()
            if "0138" in statement_text:
                bank_led = next((m for m in masters if "0138" in m), "Suspense")
        
        st.info(f"🏦 Working with: {bank_led}")
        
        if st.button("🚀 Process & Generate Tally XML"):
            xml_data = generate_safe_xml(df, bank_led, masters)
            if len(xml_data) < 500: # Check if file is empty
                st.error("❌ No data found in statement! Check your column names.")
            else:
                st.success("✅ Conversion Complete!")
                st.download_button("⬇️ Download tally_import.xml", xml_data, "tally_import.xml", "application/xml")
