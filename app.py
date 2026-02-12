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
        .bank-info { background: #E0F2FE; padding: 10px; border-radius: 8px; border-left: 5px solid #3B82F6; margin-bottom: 20px; font-weight: 600; }
    </style>
""", unsafe_allow_html=True)

# --- 2. CORE ENGINES ---
def extract_masters(html_file):
    soup = BeautifulSoup(html_file, 'html.parser')
    return sorted(list(set([td.text.strip() for td in soup.find_all('td') if len(td.text.strip()) > 1])), key=len, reverse=True)

def generate_tally_xml(rows, bank_led, masters, upi_fix="Suspense"):
    header = '<?xml version="1.0" encoding="UTF-8"?><ENVELOPE><HEADER><TALLYREQUEST>Import Data</TALLYREQUEST></HEADER><BODY><IMPORTDATA><REQUESTDESC><REPORTNAME>Vouchers</REPORTNAME><STATICVARIABLES><SVCURRENTCOMPANY/></STATICVARIABLES></REQUESTDESC><REQUESTDATA>'
    footer = '</REQUESTDATA></IMPORTDATA></BODY></ENVELOPE>'
    body = ""
    
    for row in rows:
        try:
            # Column mapping based on JANUARY 2026 STATEMENT.pdf
            # Col 2: Date, Col 4: Description, Col 5: Cr/Dr, Col 6: Amount
            dt_raw = str(row[2]).split('\n')[0].split(' ')[0]
            dt = pd.to_datetime(dt_raw, dayfirst=True).strftime('%Y%m%d')
            nar = str(row[4]).replace('\n', ' ').replace('&', '&amp;').replace('<', '&lt;')
            mode = str(row[5]).strip().upper()
            amt = float(str(row[6]).replace(',', ''))
            
            # Identity Trace
            target = "Suspense"
            for m in masters:
                if re.search(rf"\b{re.escape(m.upper())}\b", nar.upper()):
                    target = m
                    break
            if target == "Suspense" and "UPI" in nar.upper(): target = upi_fix

            # XML Construction
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
    s_file = st.file_uploader("2. Upload Statement (PDF)", type=['pdf', 'xlsx'])
    if s_file and m_file:
        all_rows = []
        with pdfplumber.open(s_file) as pdf:
            for page in pdf.pages:
                table = page.extract_table()
                if table:
                    # Skip messy headers and grab data rows
                    all_rows.extend([r for r in table if len(r) > 6 and any(char.isdigit() for char in str(r[0]))])
        
        if all_rows:
            # Auto-Detect BOB 0138 based on statement contents
            if bank_led == "⭐ Auto-Detect":
                if "090205014386" in str(all_rows) or "0138" in str(all_rows):
                    bank_led = next((m for m in masters if "0138" in m), "BOB A/C NO- 0138")
            
            st.markdown(f'<div class="bank-info">🏦 Working with: {bank_led}</div>', unsafe_allow_html=True)
            st.write(f"Found {len(all_rows)} transactions.")
            
            if st.button("🚀 Process & Generate Tally XML"):
                xml_result = generate_tally_xml(all_rows, bank_led, masters)
                st.success("✅ Conversion Complete!")
                st.download_button("⬇️ Download tally_import.xml", xml_result, "tally_import.xml", "application/xml")
        else:
            st.error("No valid transactions found. Check if the PDF is encrypted.")

st.markdown(f'<div style="position:fixed; bottom:10px; width:100%; text-align:center; font-size:12px; color:gray;">Sponsored By <b>Uday Mondal</b> | Created by <b>Debasish Biswas</b></div>', unsafe_allow_html=True)
