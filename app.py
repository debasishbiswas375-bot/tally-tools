import streamlit as st
import pandas as pd
from bs4 import BeautifulSoup
import pdfplumber
import io
import base64
import re

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(page_title="Accounting Expert", layout="wide", initial_sidebar_state="collapsed")

# --- 2. THE DESIGN (Style) ---
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
        html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #F8FAFC; }
        .hero-container { text-align: center; padding: 50px; background: linear-gradient(135deg, #065F46 0%, #1E40AF 100%); color: white; margin: -6rem -4rem 30px -4rem; }
        .stButton>button { width: 100%; background: #10B981; color: white; height: 55px; font-weight: 600; border-radius: 12px; border: none; box-shadow: 0 4px 15px rgba(16, 185, 129, 0.3); }
        .footer { position: fixed; left: 0; bottom: 0; width: 100%; background-color: white; text-align: center; padding: 10px 0; border-top: 1px solid #E2E8F0; z-index: 1000; font-size: 0.85rem; }
        .main-content { padding-bottom: 110px; }
        #MainMenu, footer, header { visibility: hidden; }
    </style>
""", unsafe_allow_html=True)

# --- 3. CORE ENGINES ---
def extract_ledgers(html_file):
    try:
        soup = BeautifulSoup(html_file, 'html.parser')
        return sorted(list(set([td.text.strip() for td in soup.find_all('td') if len(td.text.strip()) > 1])))
    except: return []

def trace_identity(narration, master_list):
    if not narration or pd.isna(narration): return "Suspense", "None"
    nar_up = str(narration).upper()
    sorted_masters = sorted(master_list, key=len, reverse=True)
    for ledger in sorted_masters:
        if re.search(rf"\b{re.escape(ledger.upper())}\b", nar_up): return ledger, "🎯 Match"
    return "Untraced", "⚠️ UPI Alert" if "UPI" in nar_up else "None"

def generate_xml(df, bank_led, synced, upi_fix=None):
    xml_header = """<?xml version="1.0"?><ENVELOPE><HEADER><TALLYREQUEST>Import Data</TALLYREQUEST></HEADER><BODY><IMPORTDATA><REQUESTDESC><REPORTNAME>Vouchers</REPORTNAME></REQUESTDESC><REQUESTDATA>"""
    xml_footer = """</REQUESTDATA></IMPORTDATA></BODY></ENVELOPE>"""
    xml_body = ""
    # Simplified logic for the body
    for _, row in df.iterrows():
        target, status = trace_identity(row.iloc[1], synced)
        if status == "⚠️ UPI Alert" and upi_fix: target = upi_fix
        # ... (Tally XML Row Construction) ...
        xml_body += f"<TALLYMESSAGE><VOUCHER><DATE>20260212</DATE><NARRATION>{row.iloc[1]}</NARRATION></VOUCHER></TALLYMESSAGE>"
    return xml_header + xml_body + xml_footer

# --- 4. UI ---
st.markdown('<div class="hero-container"><h1>Accounting Expert</h1></div>', unsafe_allow_html=True)
st.markdown('<div class="main-content">', unsafe_allow_html=True)

c1, c2 = st.columns([1, 1.5], gap="large")
with c1:
    master = st.file_uploader("Upload Tally Master", type=['html'])
    synced = extract_ledgers(master) if master else []
    bank_choice = st.selectbox("Bank Ledger", ["⭐ Auto-Detect"] + synced)

with c2:
    bank_file = st.file_uploader("Upload BOB Statement", type=['xlsx', 'xls', 'pdf'])
    if bank_file and master:
        # Load and Preview
        df = pd.read_excel(bank_file) if not bank_file.name.endswith('.pdf') else pd.DataFrame()
        st.table(df.head(5)) # Preview
        
        if st.button("🚀 Convert to Tally XML"):
            st.balloons()
            xml_data = generate_xml(df, bank_choice, synced)
            # THIS IS THE MISSING BUTTON
            st.download_button("⬇️ Download tally_import.xml", xml_data, "tally_import.xml", "application/xml")

st.markdown('<div class="footer">Sponsored By <b>Uday Mondal</b> | Created by <b>Debasish Biswas</b></div>', unsafe_allow_html=True)
