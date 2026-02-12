import streamlit as st
import pandas as pd
from bs4 import BeautifulSoup
import pdfplumber
import io
import base64
import re

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(page_title="Accounting Expert", layout="wide", initial_sidebar_state="collapsed")

# --- 2. CSS STYLING ---
st.markdown("""
    <style>
        .hero-container { text-align: center; padding: 50px; background: linear-gradient(135deg, #065F46 0%, #1E40AF 100%); color: white; margin: -6rem -4rem 30px -4rem; }
        .warning-box { background-color: #FEF2F2; border: 1px solid #EF4444; padding: 15px; border-radius: 10px; margin: 15px 0; color: #991B1B; font-weight: 600; }
        .stButton>button { width: 100%; background: #10B981; color: white; height: 50px; font-weight: 600; border-radius: 8px; border: none; }
        .footer { position: fixed; left: 0; bottom: 0; width: 100%; background-color: white; text-align: center; padding: 10px 0; border-top: 1px solid #E2E8F0; z-index: 1000; font-size: 0.85rem; }
        .main-content { padding-bottom: 110px; }
    </style>
""", unsafe_allow_html=True)

# --- 3. XML GENERATOR ENGINE ---
def generate_tally_xml(df, bank_led, synced, upi_fix_led=None):
    xml_header = """<?xml version="1.0"?><ENVELOPE><HEADER><TALLYREQUEST>Import Data</TALLYREQUEST></HEADER><BODY><IMPORTDATA><REQUESTDESC><REPORTNAME>Vouchers</REPORTNAME></REQUESTDESC><REQUESTDATA>"""
    xml_footer = """</REQUESTDATA></IMPORTDATA></BODY></ENVELOPE>"""
    xml_body = ""
    
    # Column detection
    n_c = next((c for c in df.columns if 'NARRATION' in str(c)), df.columns[1])
    dr_c = next((c for c in df.columns if 'WITHDRAWAL' in str(c)), None)
    cr_c = next((c for c in df.columns if 'DEPOSIT' in str(c)), None)
    d_c = next((c for c in df.columns if 'DATE' in str(c)), df.columns[0])

    for _, row in df.iterrows():
        try:
            val_dr = float(str(row.get(dr_c, 0)).replace(',', '')) if dr_c and row.get(dr_c) else 0
            val_cr = float(str(row.get(cr_c, 0)).replace(',', '')) if cr_c and row.get(cr_c) else 0
            # Identity logic inside XML
            target, status = trace_identity_power(row[n_c], synced)
            if status == "⚠️ UPI Alert" and upi_fix_led: target = upi_fix_led
            
            # Formatting amounts for Tally
            if val_dr > 0:
                xml_body += f"<TALLYMESSAGE><VOUCHER VCHTYPE='Payment'><DATE>20260212</DATE><NARRATION>{row[n_c]}</NARRATION><ALLLEDGERENTRIES.LIST><LEDGERNAME>{target}</LEDGERNAME><AMOUNT>-{val_dr}</AMOUNT></ALLLEDGERENTRIES.LIST><ALLLEDGERENTRIES.LIST><LEDGERNAME>{bank_led}</LEDGERNAME><AMOUNT>{val_dr}</AMOUNT></ALLLEDGERENTRIES.LIST></VOUCHER></TALLYMESSAGE>"
            elif val_cr > 0:
                xml_body += f"<TALLYMESSAGE><VOUCHER VCHTYPE='Receipt'><DATE>20260212</DATE><NARRATION>{row[n_c]}</NARRATION><ALLLEDGERENTRIES.LIST><LEDGERNAME>{bank_led}</LEDGERNAME><AMOUNT>-{val_cr}</AMOUNT></ALLLEDGERENTRIES.LIST><ALLLEDGERENTRIES.LIST><LEDGERNAME>{target}</LEDGERNAME><AMOUNT>{val_cr}</AMOUNT></ALLLEDGERENTRIES.LIST></VOUCHER></TALLYMESSAGE>"
        except: continue
    return xml_header + xml_body + xml_footer

def trace_identity_power(narration, master_list):
    if not narration or pd.isna(narration): return "Suspense", "None"
    nar_up = str(narration).upper()
    sorted_masters = sorted(master_list, key=len, reverse=True)
    for ledger in sorted_masters:
        if ledger.upper() in nar_up: return ledger, "🎯 Direct Match"
    if "UPI" in nar_up: return "Untraced", "⚠️ UPI Alert"
    return "Suspense", "None"

# (Include load_data and extract_ledger_names functions from previous conversation)

# --- 4. UI LOGIC ---
st.markdown('<div class="hero-container"><h1>Accounting Expert</h1></div>', unsafe_allow_html=True)
st.markdown('<div class="main-content">', unsafe_allow_html=True)

# ... (Settings and File Uploaders) ...

# Inside the processing logic:
if st.button("🚀 Process & Generate Tally XML"):
    st.balloons()
    # This creates the actual downloadable file
    final_xml = generate_tally_xml(df, active_bank, synced, upi_fix if 'upi_fix' in locals() else None)
    st.download_button(
        label="⬇️ Download tally_import.xml",
        data=final_xml,
        file_name="tally_import.xml",
        mime="application/xml"
    )

st.markdown('<div class="footer">Sponsored By <b>Uday Mondal</b> | Created by <b>Debasish Biswas</b></div>', unsafe_allow_html=True)
