import streamlit as st
import pandas as pd
from bs4 import BeautifulSoup
import pdfplumber
import io
import base64
import re

# --- 1. PAGE CONFIGURATION ---
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
    # Pre-sorting by length prevents 'Saha' from matching inside 'Sahanagar'
    return sorted(list(set([td.text.strip() for td in soup.find_all('td') if len(td.text.strip()) > 1])), key=len, reverse=True)

def generate_tally_xml(transactions, bank_led, masters, upi_fix="Suspense"):
    # Header matched strictly to Final_Fixed_Import.xml
    header = '<?xml version="1.0" encoding="UTF-8"?><ENVELOPE><HEADER><TALLYREQUEST>Import Data</TALLYREQUEST></HEADER><BODY><IMPORTDATA><REQUESTDESC><REPORTNAME>Vouchers</REPORTNAME><STATICVARIABLES><SVCURRENTCOMPANY/></STATICVARIABLES></REQUESTDESC><REQUESTDATA>'
    footer = '</REQUESTDATA></IMPORTDATA></BODY></ENVELOPE>'
    body = ""
    
    for row in transactions:
        try:
            # Cleaning and Formatting
            dt_raw = str(row['date']).replace('\n', '').split(' ')[0]
            dt = pd.to_datetime(dt_raw, dayfirst=True).strftime('%Y%m%d')
            nar = str(row['description']).replace('\n', ' ').replace('&', '&amp;').replace('<', '&lt;')
            mode = str(row['mode']).strip().upper()
            amt = float(str(row['amount']).replace(',', '').strip())
            
            if amt == 0: continue

            # Identity Trace
            target = "Suspense"
            for m in masters:
                if re.search(rf"\b{re.escape(m.upper())}\b", nar.upper()):
                    target = m
                    break
            if target == "Suspense" and any(k in nar.upper() for k in ["UPI", "VPA"]): target = upi_fix

            # XML Voucher logic
            vtype = "Payment" if 'DR' in mode else "Receipt"
            l1, l1_amt = (target, -amt) if 'DR' in mode else (bank_led, -amt)
            l2, l2_amt = (bank_led, amt) if 'DR' in mode else (target, amt)
            
            body += f'<TALLYMESSAGE xmlns:UDF="TallyUDF"><VOUCHER VCHTYPE="{vtype}" ACTION="Create"><DATE>{dt}</DATE><NARRATION>{nar}</NARRATION><VOUCHERTYPENAME>{vtype}</VOUCHERTYPENAME><ALLLEDGERENTRIES.LIST><LEDGERNAME>{l1}</LEDGERNAME><ISDEEMEDPOSITIVE>{"Yes" if l1_amt < 0 else "No"}</ISDEEMEDPOSITIVE><AMOUNT>{l1_amt}</AMOUNT></ALLLEDGERENTRIES.LIST><ALLLEDGERENTRIES.LIST><LEDGERNAME>{l2}</LEDGERNAME><ISDEEMEDPOSITIVE>{"Yes" if l2_amt < 0 else "No"}</ISDEEMEDPOSITIVE><AMOUNT>{l2_amt}</AMOUNT></ALLLEDGERENTRIES.LIST></VOUCHER></TALLYMESSAGE>'
        except: continue
    return header + body + footer

# --- 3. UI DASHBOARD ---
st.markdown('<div class="hero"><h1>Accounting Expert</h1></div>', unsafe_allow_html=True)

c1, c2 = st.columns([1, 1.2])
with c1:
    m_file = st.file_uploader("1. Upload Master.html", type=['html'])
    masters = extract_masters(m_file) if m_file else []
    bank_led = st.selectbox("Select Bank Ledger", ["⭐ Auto-Detect"] + masters)

with c2:
    s_file = st.file_uploader("2. Upload Statement (PDF)", type=['pdf'])
    if s_file and m_file:
        transactions = []
        with pdfplumber.open(s_file) as pdf:
            for page in pdf.pages:
                table = page.extract_table()
                if table:
                    for r in table:
                        # Logic: Valid rows start with a transaction number
                        if len(r) > 6 and r[0] and str(r[0]).strip().isdigit():
                            transactions.append({
                                'date': r[2],
                                'description': r[4],
                                'mode': r[5],
                                'amount': r[6]
                            })
        
        if transactions:
            # AUTO-DETECT: Scans for BOB Account Number 090205014386
            if bank_led == "⭐ Auto-Detect":
                bank_led = next((m for m in masters if "0138" in m), "BOB A/C NO- 0138")
            
            st.info(f"🏦 Working with: {bank_led}")
            
            if st.button("🚀 Process & Generate Tally XML"):
                xml_result = generate_tally_xml(transactions, bank_led, masters)
                if len(xml_result) > 1000:
                    st.success(f"✅ Success! Captured {len(transactions)} entries.")
                    st.download_button("⬇️ Download tally_import.xml", xml_result, "tally_import.xml", "application/xml")
                else:
                    st.error("XML is too small. Check mapping.")
        else:
            st.error("No valid data rows found in PDF.")

st.markdown(f'<div style="position:fixed; bottom:10px; width:100%; text-align:center; font-size:12px; color:gray;">Sponsored By <b>Uday Mondal</b> | Created by <b>Debasish Biswas</b></div>', unsafe_allow_html=True)
