import streamlit as st
import pandas as pd
from bs4 import BeautifulSoup
import pdfplumber
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

# --- 2. PREMIUM UI & PINNED FOOTER CSS ---
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
        html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #F8FAFC; }
        .hero-container { text-align: center; padding: 50px; background: linear-gradient(135deg, #065F46 0%, #1E40AF 100%); color: white; margin: -6rem -4rem 30px -4rem; }
        .bank-detect-box { background-color: #E0F2FE; border: 2px solid #3B82F6; padding: 15px; border-radius: 10px; color: #1E3A8A; font-weight: 700; margin-bottom: 20px; text-align: center; font-size: 1.1rem; }
        .warning-box { background-color: #FEF2F2; border: 2px solid #EF4444; padding: 20px; border-radius: 12px; margin: 20px 0; color: #991B1B; }
        .stButton>button { width: 100%; background: #10B981; color: white; height: 55px; font-weight: 600; border-radius: 8px; border: none; box-shadow: 0 4px 15px rgba(16, 185, 129, 0.3); }
        
        /* PINNED FOOTER CSS */
        .footer { 
            position: fixed; 
            left: 0; 
            bottom: 0; 
            width: 100%; 
            background-color: white; 
            color: #64748B; 
            text-align: center; 
            padding: 15px; 
            border-top: 1px solid #E2E8F0; 
            z-index: 1000;
            box-shadow: 0 -2px 10px rgba(0,0,0,0.05);
        }
        .main { padding-bottom: 100px; } /* Space for pinned footer */
        #MainMenu, footer, header { visibility: hidden; }
    </style>
""", unsafe_allow_html=True)

# --- 3. CORE ENGINE (Identity Separation & XML Generator) ---

def extract_ledger_names(html_file):
    try:
        soup = BeautifulSoup(html_file, 'html.parser')
        return sorted(list(set([td.text.strip() for td in soup.find_all('td') if len(td.text.strip()) > 1])))
    except: return []

def trace_identity_power(narration, master_list):
    """Matches longest names first (Mithu Mondal before Mithu) with word boundaries."""
    if not narration or pd.isna(narration): return "Suspense", "None"
    nar_up = str(narration).upper().replace('/', ' ')
    sorted_masters = sorted(master_list, key=len, reverse=True)
    for ledger in sorted_masters:
        pattern = rf"\b{re.escape(ledger.upper())}\b"
        if re.search(pattern, nar_up):
            return ledger, "🎯 Exact Identity"
    if "UPI" in nar_up: return "Untraced", "⚠️ UPI Alert"
    return "Suspense", "None"

def generate_tally_xml(df, bank_led, synced, upi_fix_led=None):
    """FIXED: Uses 'good one.xml' signage (Debit=Yes/-Amt) to ensure import works."""
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
            nar = str(row.get(n_c, '')).replace('&', '&amp;')
            dt = pd.to_datetime(row.get(d_c)).strftime("%Y%m%d") if row.get(d_c) else "20260101"

            if val_dr > 0:
                vch, amt = "Payment", val_dr
                target, status = trace_identity_power(row[n_c], synced)
                if status == "UPI_Alert" and upi_fix_led: target = upi_fix_led
                l1, l1_pos, l1_amt = (target, "Yes", -amt), (bank_led, "No", amt)
            elif val_cr > 0:
                vch, amt = "Receipt", val_cr
                target, status = trace_identity_power(row[n_c], synced)
                if status == "UPI_Alert" and upi_fix_led: target = upi_fix_led
                l1, l1_pos, l1_amt = (bank_led, "Yes", -amt), (target, "No", amt)
            else: continue

            xml_body += f"""<TALLYMESSAGE xmlns:UDF="TallyUDF"><VOUCHER VCHTYPE="{vch}" ACTION="Create"><DATE>{dt}</DATE><NARRATION>{nar}</NARRATION><VOUCHERTYPENAME>{vch}</VOUCHERTYPENAME><ALLLEDGERENTRIES.LIST><LEDGERNAME>{l1[0]}</LEDGERNAME><ISDEEMEDPOSITIVE>{l1[1]}</ISDEEMEDPOSITIVE><AMOUNT>{l1[2]}</AMOUNT></ALLLEDGERENTRIES.LIST><ALLLEDGERENTRIES.LIST><LEDGERNAME>{l1_pos[0]}</LEDGERNAME><ISDEEMEDPOSITIVE>{l1_pos[1]}</ISDEEMEDPOSITIVE><AMOUNT>{l1_pos[2]}</AMOUNT></ALLLEDGERENTRIES.LIST></VOUCHER></TALLYMESSAGE>"""
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

# --- 4. UI DASHBOARD ---
st.markdown('<div class="hero-container"><h1>Accounting Expert</h1><p>Identity Separation: Mithu Sk vs Mithu Mondal</p></div>', unsafe_allow_html=True)
c1, c2 = st.columns([1, 1.5], gap="large")

with c1:
    st.markdown("### 🛠️ 1. Settings")
    master_file = st.file_uploader("Upload Tally Master", type=['html'])
    synced, options = [], ["Upload Master first"]
    if master_file:
        synced = extract_ledger_names(master_file)
        st.success(f"✅ {len(synced)} Ledgers Synced")
        options = ["⭐ Auto-Select Bank"] + synced
    bank_choice = st.selectbox("Select Bank Ledger", options)

with c2:
    st.markdown("### 📂 2. Convert & Preview")
    bank_file = st.file_uploader("Drop Statement here", type=['xlsx', 'xls'])
    if bank_file and master_file:
        df = load_data(bank_file)
        if df is not None:
            active_bank = bank_choice
            meta = str(df.iloc[:10].values).upper()
            if "BOB" in meta or "138" in meta:
                active_bank = next((l for l in synced if any(k in l.upper() for k in ["BOB", "BARODA", "138"])), bank_choice)
                st.markdown(f'<div class="bank-detect-box">🏦 Auto-Detected BOB Ledger: {active_bank}</div>', unsafe_allow_html=True)

            n_col = next((c for c in df.columns if 'NARRATION' in str(c)), df.columns[1])
            unmatched_upi = [idx for idx, row in df.iterrows() if trace_identity_power(row[n_col], synced)[1] == "UPI Alert"]
            
            if len(unmatched_upi) > 5:
                st.markdown(f'<div class="warning-box">⚠️ Interaction Required: {len(unmatched_upi)} unknown UPIs.</div>', unsafe_allow_html=True)
                upi_fix = st.selectbox("Assign untraced UPIs to:", synced)
                if st.button("🚀 Process & Create Tally XML"):
                    xml_data = generate_tally_xml(df, active_bank, synced, upi_fix)
                    st.balloons() # CONGRATULATIONS ANIMATION
                    st.download_button("⬇️ Download tally_import.xml", xml_data, file_name="tally_import.xml")
            else:
                if st.button("🚀 Convert to Tally XML"):
                    xml_data = generate_tally_xml(df, active_bank, synced)
                    st.balloons() # CONGRATULATIONS ANIMATION
                    st.download_button("⬇️ Download tally_import.xml", xml_data, file_name="tally_import.xml")

# --- 5. PINNED BRANDED FOOTER ---
st.markdown(f"""
    <div class="footer">
        <p>Sponsored By <b>Uday Mondal</b> | Consultant Advocate</p>
        <p style="font-size: 13px; margin-top:-10px;">Powered & Created by <b>Debasish Biswas</b></p>
    </div>
""", unsafe_allow_html=True)
