import streamlit as st
import pandas as pd
from bs4 import BeautifulSoup
import io
import base64
import re

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Accounting Expert | AI Bank to Tally",
    page_icon="logo.png",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 2. UI & PINNED FOOTER CSS ---
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
        html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #F8FAFC; }
        .hero-container { text-align: center; padding: 40px; background: linear-gradient(135deg, #065F46 0%, #1E40AF 100%); color: white; margin: -6rem -4rem 20px -4rem; }
        .bank-detect-box { background-color: #E0F2FE; border: 1px solid #3B82F6; padding: 12px; border-radius: 8px; color: #1E3A8A; font-weight: 700; margin-top: 10px; margin-bottom: 20px; text-align: center; border-left: 5px solid #3B82F6; }
        .warning-box { background-color: #FEF2F2; border: 1px solid #EF4444; padding: 15px; border-radius: 8px; margin: 15px 0; color: #991B1B; font-weight: 600; }
        .footer { position: fixed; left: 0; bottom: 0; width: 100%; background-color: white; color: #64748B; text-align: center; padding: 10px 0; border-top: 1px solid #E2E8F0; z-index: 1000; font-size: 0.85rem; }
        .main-content { padding-bottom: 110px; }
        #MainMenu, footer, header { visibility: hidden; }
    </style>
""", unsafe_allow_html=True)

# --- 3. ENGINE ---
def extract_ledger_names(html_file):
    try:
        soup = BeautifulSoup(html_file, 'html.parser')
        return sorted(list(set([td.text.strip() for td in soup.find_all('td') if len(td.text.strip()) > 1])))
    except: return []

def trace_identity_power(narration, master_list):
    if not narration or pd.isna(narration): return "Suspense", "None"
    nar_up = str(narration).upper().replace('/', ' ')
    sorted_masters = sorted(master_list, key=len, reverse=True)
    for ledger in sorted_masters:
        pattern = rf"\b{re.escape(ledger.upper())}\b"
        if re.search(pattern, nar_up): return ledger, "🎯 Direct Match"
    if "UPI" in nar_up: return "Untraced", "⚠️ UPI Alert"
    return "Suspense", "None"

def generate_tally_xml(df, bank_led, synced, upi_fix_led=None):
    xml_header = """<?xml version="1.0"?><ENVELOPE><HEADER><TALLYREQUEST>Import Data</TALLYREQUEST></HEADER><BODY><IMPORTDATA><REQUESTDESC><REPORTNAME>Vouchers</REPORTNAME></REQUESTDESC><REQUESTDATA>"""
    xml_footer = """</REQUESTDATA></IMPORTDATA></BODY></ENVELOPE>"""
    xml_body = ""
    n_c = next((c for c in df.columns if 'NARRATION' in str(c)), df.columns[1])
    dr_c = next((c for c in df.columns if 'WITHDRAWAL' in str(c) or 'DEBIT' in str(c)), None)
    cr_c = next((c for c in df.columns if 'DEPOSIT' in str(c) or 'CREDIT' in str(c)), None)
    d_c = next((c for c in df.columns if 'DATE' in str(c)), df.columns[0])
    for _, row in df.iterrows():
        try:
            val_dr = float(str(row.get(dr_c, 0)).replace(',', '')) if dr_c and row.get(dr_c) else 0
            val_cr = float(str(row.get(cr_c, 0)).replace(',', '')) if cr_c and row.get(cr_c) else 0
            nar = str(row.get(n_c, '')).replace('&', '&amp;').replace('<', '&lt;')
            dt = pd.to_datetime(row.get(d_c)).strftime("%Y%m%d")
            target, status = trace_identity_power(row[n_c], synced)
            if status == "⚠️ UPI Alert" and upi_fix_led: target = upi_fix_led
            if val_dr > 0:
                l1_n, l1_p, l1_a = target, "Yes", -val_dr
                l2_n, l2_p, l2_a = bank_led, "No", val_dr
            elif val_cr > 0:
                l1_n, l1_p, l1_a = bank_led, "Yes", -val_cr
                l2_n, l2_p, l2_a = target, "No", val_cr
            else: continue
            xml_body += f"""<TALLYMESSAGE xmlns:UDF="TallyUDF"><VOUCHER VCHTYPE="As Per Row" ACTION="Create"><DATE>{dt}</DATE><NARRATION>{nar}</NARRATION><ALLLEDGERENTRIES.LIST><LEDGERNAME>{l1_n}</LEDGERNAME><ISDEEMEDPOSITIVE>{l1_p}</ISDEEMEDPOSITIVE><AMOUNT>{l1_a}</AMOUNT></ALLLEDGERENTRIES.LIST><ALLLEDGERENTRIES.LIST><LEDGERNAME>{l2_n}</LEDGERNAME><ISDEEMEDPOSITIVE>{l2_p}</ISDEEMEDPOSITIVE><AMOUNT>{l2_a}</AMOUNT></ALLLEDGERENTRIES.LIST></VOUCHER></TALLYMESSAGE>"""
        except: continue
    return xml_header + xml_body + xml_footer

def load_data(file):
    try:
        df = pd.read_excel(file, header=None)
        for i, row in df.iterrows():
            row_str = " ".join([str(x).lower() for x in row if x])
            if 'narration' in row_str and 'tran date' in row_str:
                df.columns = [str(c).strip().upper() for c in df.iloc[i]]
                return df[i+1:].reset_index(drop=True).dropna(subset=[df.columns[1]], thresh=1)
        return None
    except: return None

# --- UI ---
st.markdown('<div class="hero-container"><h1>Accounting Expert</h1></div>', unsafe_allow_html=True)
st.markdown('<div class="main-content">', unsafe_allow_html=True)
c1, c2 = st.columns([1, 1.5], gap="large")

with c1:
    st.markdown("### 🛠️ 1. Settings")
    master = st.file_uploader("Upload Tally Master (HTML)", type=['html'])
    synced, options = [], ["Upload Master first"]
    if master:
        synced = extract_ledger_names(master)
        st.toast(f"✅ {len(synced)} Ledgers Synced Successfully!")
        options = ["⭐ Auto-Select Bank"] + synced
    bank_choice = st.selectbox("Select Bank Ledger", options)

with c2:
    st.markdown("### 📂 2. Convert & Preview")
    bank_file = st.file_uploader("Upload BOB Statement", type=['xlsx', 'xls'])
    if bank_file and master:
        df = load_data(bank_file)
        if df is not None:
            active_bank = bank_choice
            if bank_choice == "⭐ Auto-Select Bank":
                meta = str(df.iloc[:10].values).upper()
                if any(k in meta for k in ["BOB", "BARODA", "138"]):
                    active_bank = next((l for l in synced if any(k in l.upper() for k in ["BOB", "BARODA", "138"])), bank_choice)
            st.markdown(f'<div class="bank-detect-box">🏦 Selected Bank Account: <b>{active_bank}</b></div>', unsafe_allow_html=True)
            n_c = next((c for c in df.columns if 'NARRATION' in str(c)), df.columns[1])
            unmatched_upi = [idx for idx, r in df.iterrows() if trace_identity_power(r[n_c], synced)[1] == "⚠️ UPI Alert"]
            if len(unmatched_upi) > 5:
                st.markdown(f'<div class="warning-box">⚠️ Action Required: {len(unmatched_upi)} Untraced UPI entries.</div>', unsafe_allow_html=True)
                upi_fix = st.selectbox("Assign unknown UPIs to:", synced)
                if st.button("🚀 Process & Create Tally XML"):
                    st.balloons()
                    st.download_button("⬇️ Download tally_import.xml", generate_tally_xml(df, active_bank, synced, upi_fix), file_name="tally_import.xml")
            else:
                if st.button("🚀 Convert to Tally XML"):
                    st.balloons()
                    st.download_button("⬇️ Download tally_import.xml", generate_tally_xml(df, active_bank, synced), file_name="tally_import.xml")

st.markdown(f'<div class="footer">Sponsored By <b>Uday Mondal</b> (Advocate) | Created by <b>Debasish Biswas</b></div>', unsafe_allow_html=True)
