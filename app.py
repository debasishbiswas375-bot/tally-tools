import streamlit as st
import pandas as pd
from bs4 import BeautifulSoup
import pdfplumber
import io
import base64
import re

# --- 1. PAGE CONFIG ---
st.set_page_config(page_title="Accounting Expert", layout="wide", initial_sidebar_state="collapsed")

# --- 2. CSS STYLE (Pinned Footer & Hero) ---
st.markdown("""
    <style>
        .hero-container { text-align: center; padding: 40px; background: linear-gradient(135deg, #065F46 0%, #1E40AF 100%); color: white; margin: -6rem -4rem 20px -4rem; }
        .footer { position: fixed; left: 0; bottom: 0; width: 100%; background-color: white; text-align: center; padding: 10px 0; border-top: 1px solid #E2E8F0; z-index: 1000; font-size: 0.85rem; }
        .stButton>button { width: 100%; background: #10B981; color: white; height: 50px; font-weight: 600; border-radius: 8px; border: none; }
        .main-content { padding-bottom: 100px; }
    </style>
""", unsafe_allow_html=True)

# --- 3. FAST XML ENGINE ---
def generate_tally_xml(df, bank_led, synced, upi_fix=None):
    xml_start = '<?xml version="1.0"?><ENVELOPE><HEADER><TALLYREQUEST>Import Data</TALLYREQUEST></HEADER><BODY><IMPORTDATA><REQUESTDESC><REPORTNAME>Vouchers</REPORTNAME></REQUESTDESC><REQUESTDATA>'
    xml_end = '</REQUESTDATA></IMPORTDATA></BODY></ENVELOPE>'
    xml_body = ""
    
    # Pre-sort masters for speed
    sorted_masters = sorted(synced, key=len, reverse=True)

    for idx, row in df.iterrows():
        nar = str(row.iloc[1]).upper()
        target = "Suspense"
        
        # Fast Matching
        for m in sorted_masters:
            if m.upper() in nar:
                target = m
                break
        
        if target == "Suspense" and upi_fix and "UPI" in nar:
            target = upi_fix

        # Create Row (Simplified for speed)
        xml_body += f"<TALLYMESSAGE><VOUCHER><DATE>20260212</DATE><NARRATION>{nar}</NARRATION><ALLLEDGERENTRIES.LIST><LEDGERNAME>{target}</LEDGERNAME><AMOUNT>-100</AMOUNT></ALLLEDGERENTRIES.LIST></VOUCHER></TALLYMESSAGE>"
    
    return xml_start + xml_body + xml_end

# --- 4. UI ---
st.markdown('<div class="hero-container"><h1>Accounting Expert</h1></div>', unsafe_allow_html=True)
st.markdown('<div class="main-content">', unsafe_allow_html=True)

c1, c2 = st.columns([1, 1.5])

with c1:
    st.write("### 🛠️ 1. Settings")
    master = st.file_uploader("Upload Master.html", type=['html'])
    synced = []
    if master:
        soup = BeautifulSoup(master, 'html.parser')
        synced = [td.text.strip() for td in soup.find_all('td') if len(td.text.strip()) > 1]
    bank_choice = st.selectbox("Bank Ledger", synced if synced else ["Upload Master first"])

with c2:
    st.write("### 📂 2. Convert & Download")
    file = st.file_uploader("Upload Statement", type=['xlsx', 'pdf'])
    
    if file and master:
        # Load data (Optimized)
        if file.name.endswith('.pdf'):
            with pdfplumber.open(file) as pdf:
                df = pd.DataFrame([r for p in pdf.pages for r in (p.extract_table() or [])])
        else:
            df = pd.read_excel(file)

        st.dataframe(df.head(5), use_container_width=True)

        # THE CONVERT & DOWNLOAD BUTTONS
        if st.button("🚀 Start Conversion"):
            with st.spinner("Processing..."):
                xml_result = generate_tally_xml(df, bank_choice, synced)
                st.balloons()
                st.success("Conversion Finished!")
                
                # THE DOWNLOAD BUTTON (Now clearly visible)
                st.download_button(
                    label="⬇️ DOWNLOAD TALLY XML FILE",
                    data=xml_result,
                    file_name="tally_import.xml",
                    mime="application/xml"
                )

st.markdown('</div>', unsafe_allow_html=True)
st.markdown('<div class="footer">Sponsored By <b>Uday Mondal</b> | Created by <b>Debasish Biswas</b></div>', unsafe_allow_html=True)
