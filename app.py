import streamlit as st
import pandas as pd
from bs4 import BeautifulSoup
import pdfplumber
import io
import base64
import re

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(page_title="Accounting Expert", layout="wide", initial_sidebar_state="collapsed")

# --- 2. IMAGE HANDLER ---
def get_img_as_base64(file):
    try:
        with open(file, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except: return None

# --- 3. STYLE (Old Design) ---
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
        html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #F8FAFC; }
        .hero-container { text-align: center; padding: 50px; background: linear-gradient(135deg, #065F46 0%, #1E40AF 100%); color: white; margin: -6rem -4rem 30px -4rem; }
        .bank-detect-box { background-color: #E0F2FE; border: 1px solid #3B82F6; padding: 15px; border-radius: 12px; color: #1E3A8A; font-weight: 700; margin-bottom: 20px; text-align: center; border-left: 8px solid #3B82F6; }
        .warning-box { background-color: #FEF2F2; border: 1px solid #EF4444; padding: 15px; border-radius: 10px; margin: 15px 0; color: #991B1B; font-weight: 600; border-left: 8px solid #EF4444; }
        .stButton>button { width: 100%; background: #10B981; color: white; height: 55px; font-weight: 600; border-radius: 12px; border: none; box-shadow: 0 4px 15px rgba(16, 185, 129, 0.3); }
        .footer { position: fixed; left: 0; bottom: 0; width: 100%; background-color: white; color: #64748B; text-align: center; padding: 12px 0; border-top: 1px solid #E2E8F0; z-index: 1000; font-size: 0.85rem; }
        .main-content { padding-bottom: 120px; }
        #MainMenu, footer, header { visibility: hidden; }
    </style>
""", unsafe_allow_html=True)

# --- 4. TALLY XML ENGINE ---
def create_tally_xml(df, bank_led, synced, upi_fix=None):
    xml_start = '<?xml version="1.0"?><ENVELOPE><HEADER><TALLYREQUEST>Import Data</TALLYREQUEST></HEADER><BODY><IMPORTDATA><REQUESTDESC><REPORTNAME>Vouchers</REPORTNAME></REQUESTDESC><REQUESTDATA>'
    xml_end = '</REQUESTDATA></IMPORTDATA></BODY></ENVELOPE>'
    xml_content = ""
    
    n_col = next((c for c in df.columns if 'NARRATION' in str(c)), df.columns[1])
    dr_col = next((c for c in df.columns if 'WITHDRAWAL' in str(c)), None)
    cr_col = next((c for c in df.columns if 'DEPOSIT' in str(c)), None)
    d_col = next((c for c in df.columns if 'DATE' in str(c)), df.columns[0])

    for _, row in df.iterrows():
        try:
            nar = str(row[n_col]).replace('&', '&amp;')
            dt = pd.to_datetime(row[d_col]).strftime('%Y%m%d')
            dr_val = float(str(row.get(dr_col, 0)).replace(',', '')) if dr_col and row[dr_col] else 0
            cr_val = float(str(row.get(cr_col, 0)).replace(',', '')) if cr_col and row[cr_col] else 0
            
            target, status = trace_identity(nar, synced)
            if status == "⚠️ UPI Alert" and upi_fix: target = upi_fix
            
            if dr_val > 0: # Payment
                xml_content += f'<TALLYMESSAGE xmlns:UDF="TallyUDF"><VOUCHER VCHTYPE="Payment" ACTION="Create"><DATE>{dt}</DATE><NARRATION>{nar}</NARRATION><ALLLEDGERENTRIES.LIST><LEDGERNAME>{target}</LEDGERNAME><ISDEEMEDPOSITIVE>Yes</ISDEEMEDPOSITIVE><AMOUNT>-{dr_val}</AMOUNT></ALLLEDGERENTRIES.LIST><ALLLEDGERENTRIES.LIST><LEDGERNAME>{bank_led}</LEDGERNAME><ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE><AMOUNT>{dr_val}</AMOUNT></ALLLEDGERENTRIES.LIST></VOUCHER></TALLYMESSAGE>'
            elif cr_val > 0: # Receipt
                xml_content += f'<TALLYMESSAGE xmlns:UDF="TallyUDF"><VOUCHER VCHTYPE="Receipt" ACTION="Create"><DATE>{dt}</DATE><NARRATION>{nar}</NARRATION><ALLLEDGERENTRIES.LIST><LEDGERNAME>{bank_led}</LEDGERNAME><ISDEEMEDPOSITIVE>Yes</ISDEEMEDPOSITIVE><AMOUNT>-{cr_val}</AMOUNT></ALLLEDGERENTRIES.LIST><ALLLEDGERENTRIES.LIST><LEDGERNAME>{target}</LEDGERNAME><ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE><AMOUNT>{cr_val}</AMOUNT></ALLLEDGERENTRIES.LIST></VOUCHER></TALLYMESSAGE>'
        except: continue
    return xml_start + xml_content + xml_end

def trace_identity(nar, masters):
    nar_up = str(nar).upper()
    sorted_m = sorted(masters, key=len, reverse=True)
    for m in sorted_m:
        if re.search(rf"\b{re.escape(m.upper())}\b", nar_up): return m, "🎯 Match"
    return "Untraced", "⚠️ UPI Alert" if "UPI" in nar_up else "None"

def load_data(file):
    try:
        if file.name.endswith('.pdf'):
            with pdfplumber.open(file) as pdf:
                all_data = [r for p in pdf.pages for r in (p.extract_table() or [])]
            df = pd.DataFrame(all_data)
        else:
            df = pd.read_excel(file, header=None)
        for i, row in df.iterrows():
            if 'narration' in " ".join([str(x).lower() for x in row if x]):
                df.columns = [str(c).strip().upper() for c in df.iloc[i]]
                return df[i+1:].reset_index(drop=True).dropna(subset=[df.columns[1]], thresh=1), df.iloc[:i]
        return None, None
    except: return None, None

# --- 5. UI ---
l_top = get_img_as_base64("logo.png")
st.markdown(f'<div class="hero-container">{f"<img src=\'data:image/png;base64,{l_top}\' width=\'80\'>" if l_top else ""}<h1>Accounting Expert</h1></div>', unsafe_allow_html=True)

st.markdown('<div class="main-content">', unsafe_allow_html=True)
c1, c2 = st.columns([1, 1.5], gap="large")

with c1:
    st
