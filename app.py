import streamlit as st
import pandas as pd
from bs4 import BeautifulSoup
import pdfplumber
import io
import base64
import re

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(page_title="Accounting Expert", layout="wide", initial_sidebar_state="collapsed")

# --- 2. UI & FOOTER CSS ---
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
        html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #F8FAFC; }
        .hero-container { text-align: center; padding: 40px; background: linear-gradient(135deg, #065F46 0%, #1E40AF 100%); color: white; margin: -6rem -4rem 20px -4rem; }
        .bank-detect-box { background-color: #E0F2FE; border: 2px solid #3B82F6; padding: 15px; border-radius: 10px; color: #1E3A8A; font-weight: 700; margin-bottom: 20px; text-align: center; border-left: 8px solid #3B82F6; }
        .warning-box { background-color: #FEF2F2; border: 1px solid #EF4444; padding: 15px; border-radius: 8px; margin: 15px 0; color: #991B1B; font-weight: 600; }
        .stButton>button { width: 100%; background: #10B981; color: white; height: 50px; font-weight: 600; border-radius: 8px; border: none; box-shadow: 0 4px 12px rgba(16, 185, 129, 0.2); }
        .footer { position: fixed; left: 0; bottom: 0; width: 100%; background-color: white; color: #64748B; text-align: center; padding: 10px 0; border-top: 1px solid #E2E8F0; z-index: 1000; font-size: 0.85rem; }
        .main-content { padding-bottom: 110px; }
        #MainMenu, footer, header { visibility: hidden; }
    </style>
""", unsafe_allow_html=True)

# --- 3. CORE ENGINE ---

def extract_ledger_names(html_file):
    try:
        soup = BeautifulSoup(html_file, 'html.parser')
        raw_ledgers = list(set([td.text.strip() for td in soup.find_all('td') if len(td.text.strip()) > 1]))
        # FILTER: Remove Banks/Cash from Party List to solve your "selecting all master" issue
        party_ledgers = [l for l in raw_ledgers if not any(x in l.upper() for x in ["BANK", "CASH", "SBI", "BOB", "IFSC", "A/C"])]
        bank_ledgers = [l for l in raw_ledgers if any(x in l.upper() for x in ["BANK", "SBI", "BOB"])]
        return sorted(party_ledgers), sorted(bank_ledgers)
    except: return [], []

def trace_identity_power(narration, master_list):
    """Deep Trace: Matches longest phrases (Mithu Mondal) and avoids partials (Saha)."""
    if not narration or pd.isna(narration): return "Suspense", "None"
    nar_up = str(narration).upper().replace('/', ' ')
    sorted_masters = sorted(master_list, key=len, reverse=True)
    for ledger in sorted_masters:
        pattern = rf"\b{re.escape(ledger.upper())}\b"
        if re.search(pattern, nar_up): return ledger, "🎯 Direct Match"
    if "UPI" in nar_up: return "Untraced", "⚠️ UPI Alert"
    return "Suspense", "None"

def generate_tally_xml(df, bank_led, synced_parties):
    xml_header = """<?xml version="1.0"?><ENVELOPE><HEADER><TALLYREQUEST>Import Data</TALLYREQUEST></HEADER><BODY><IMPORTDATA><REQUESTDESC><REPORTNAME>Vouchers</REPORTNAME></REQUESTDESC><REQUESTDATA>"""
    xml_footer = """</REQUESTDATA></IMPORTDATA></BODY></ENVELOPE>"""
    xml_body = ""
    n_c = next((c for c in df.columns if 'NARRATION' in str(c)), df.columns[1])
    dr_c = next((c for c in df.columns if 'WITHDRAWAL' in str(c)), None)
    cr_c = next((c for c in df.columns if 'DEPOSIT' in str(c)), None)
    d_c = next((c for c in df.columns if 'DATE' in str(c)), df.columns[0])

    for _, row in df.iterrows():
        try:
            val_dr = float(str(row.get(dr_c, 0)).replace(',', '')) if dr_c and row.get(dr_c) else 0
            val_cr = float(str(row.get(cr_c, 0)).replace(',', '')) if cr_c and row.get(cr_c) else 0
            dt = pd.to_datetime(row.get(d_c)).strftime("%Y%m%d")
            target, _ = trace_identity_power(row[n_c], synced_parties)
            
            if val_dr > 0:
                l1, l2, vch = (target, "Yes", -val_dr), (bank_led, "No", val_dr), "Payment"
            elif val_cr > 0:
                l1, l2, vch = (bank_led, "Yes", -val_cr), (target, "No", val_cr), "Receipt"
            else: continue

            xml_body += f"""<TALLYMESSAGE xmlns:UDF="TallyUDF"><VOUCHER VCHTYPE="{vch}" ACTION="Create"><DATE>{dt}</DATE><NARRATION>{row[n_c]}</NARRATION><ALLLEDGERENTRIES.LIST><LEDGERNAME>{l1[0]}</LEDGERNAME><ISDEEMEDPOSITIVE>{l1[1]}</ISDEEMEDPOSITIVE><AMOUNT>{l1[2]}</AMOUNT></ALLLEDGERENTRIES.LIST><ALLLEDGERENTRIES.LIST><LEDGERNAME>{l2[0]}</LEDGERNAME><ISDEEMEDPOSITIVE>{l2[1]}</ISDEEMEDPOSITIVE><AMOUNT>{l2[2]}</AMOUNT></ALLLEDGERENTRIES.LIST></VOUCHER></TALLYMESSAGE>"""
        except: continue
    return xml_header + xml_body + xml_footer

def load_data(file):
    try:
        if file.name.lower().endswith('.pdf'):
            with pdfplumber.open(file) as pdf:
                all_text = []
                for page in pdf.pages:
                    table = page.extract_table()
                    if table: all_text.extend(table)
            df = pd.DataFrame(all_text)
        else:
            df = pd.read_excel(file, header=None)
        
        for i, row in df.iterrows():
            row_str = " ".join([str(x).lower() for x in row if x])
            if 'narration' in row_str:
                df.columns = [str(c).strip().upper() for c in df.iloc[i]]
                return df[i+1:].reset_index(drop=True).dropna(subset=[df.columns[1]], thresh=1), df.iloc[:i]
        return None, None
    except: return None, None

# --- UI ---
st.markdown('<div class="hero-container"><h1>Accounting Expert</h1></div>', unsafe_allow_html=True)
st.markdown('<div class="main-content">', unsafe_allow_html=True)
c1, c2 = st.columns([1, 1.5], gap="large")

with c1:
    st.markdown("### 🛠️ 1. Settings")
    master = st.file_uploader("Upload Tally Master", type=['html'])
    parties, banks = [], []
    if master:
        parties, banks = extract_ledger_names(master)
        st.toast(f"✅ {len(parties)} Parties & {len(banks)} Banks Synced!")
    
    bank_choice = st.selectbox("Select Bank Ledger", ["⭐ Auto-Select"] + banks)

with c2:
    st.markdown("### 📂 2. Convert & Preview")
    bank_file = st.file_uploader("Upload BOB Statement", type=['xlsx', 'xls', 'pdf'])
    if bank_file and master:
        df, meta = load_data(bank_file)
        if df is not None:
            active_bank = bank_choice
            if bank_choice == "⭐ Auto-Select":
                full_txt = " ".join(meta.astype(str).values.flatten()).upper()
                active_bank = next((l for l in banks if any(k in full_txt or k in l.upper() for k in ["BOB", "138", "BARODA"])), "Bank of Baroda")
            
            st.markdown(f'<div class="bank-detect-box">🏦 Bank Ledger Selected: <b>{active_bank}</b></div>', unsafe_allow_html=True)
            
            n_c = next((c for c in df.columns if 'NARRATION' in str(c)), df.columns[1])
            st.markdown("### 📋 Smart Identity Preview")
            preview = [{"Narration": str(row[n_c])[:50], "Tally Target": trace_identity_power(row[n_c], parties)[0]} for _, row in df.head(10).iterrows()]
            st.table(preview)

            if st.button("🚀 Convert to Tally XML"):
                st.balloons()
                st.download_button("⬇️ Download", generate_tally_xml(df, active_bank, parties), file_name="tally.xml")

st.markdown(f'<div class="footer">Sponsored By <b>Uday Mondal</b> | Created by <b>Debasish Biswas</b></div>', unsafe_allow_html=True)
