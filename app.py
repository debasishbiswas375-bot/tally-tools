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

# --- 2. PREMIUM UI & SLIM PINNED FOOTER CSS ---
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
        html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #F8FAFC; }
        
        .hero-container { text-align: center; padding: 40px; background: linear-gradient(135deg, #065F46 0%, #1E40AF 100%); color: white; margin: -6rem -4rem 20px -4rem; }
        .bank-detect-box { background-color: #E0F2FE; border: 1px solid #3B82F6; padding: 12px; border-radius: 8px; color: #1E3A8A; font-weight: 700; margin-top: 10px; margin-bottom: 20px; text-align: center; border-left: 5px solid #3B82F6; }
        .warning-box { background-color: #FEF2F2; border: 1px solid #EF4444; padding: 15px; border-radius: 8px; margin: 15px 0; color: #991B1B; font-size: 0.9rem; }
        
        .stButton>button { width: 100%; background: #10B981; color: white; height: 50px; font-weight: 600; border-radius: 8px; border: none; box-shadow: 0 4px 12px rgba(16, 185, 129, 0.2); }
        
        /* SLIM PINNED FOOTER */
        .footer { 
            position: fixed; 
            left: 0; 
            bottom: 0; 
            width: 100%; 
            background-color: white; 
            color: #64748B; 
            text-align: center; 
            padding: 10px 0; 
            border-top: 1px solid #E2E8F0; 
            z-index: 1000;
            font-size: 0.85rem;
        }
        .footer b { color: #0F172A; }
        
        /* Layout Padding */
        .main-content { padding-bottom: 110px; }
        #MainMenu, footer, header { visibility: hidden; }
    </style>
""", unsafe_allow_html=True)

# --- 3. CORE ENGINE ---

def get_img_as_base64(file):
    try:
        with open(file, "rb") as f: return base64.b64encode(f.read()).decode()
    except: return None

def extract_ledger_names(html_file):
    try:
        soup = BeautifulSoup(html_file, 'html.parser')
        # Extracts unique ledger names from Tally Master HTML
        return sorted(list(set([td.text.strip() for td in soup.find_all('td') if len(td.text.strip()) > 1])))
    except: return []

def trace_identity_power(narration, master_list):
    """Deep Trace: Matches longest names first (Mithu Mondal > Mithu Sk > Mithu)"""
    if not narration or pd.isna(narration): return "Suspense", "None"
    nar_up = str(narration).upper().replace('/', ' ')
    sorted_masters = sorted(master_list, key=len, reverse=True)
    for ledger in sorted_masters:
        pattern = rf"\b{re.escape(ledger.upper())}\b"
        if re.search(pattern, nar_up):
            return ledger, "🎯 Direct Match"
    if "UPI" in nar_up: return "Untraced", "⚠️ UPI Alert"
    return "Suspense", "None"

def generate_tally_xml(df, bank_led, synced, upi_fix_led=None):
    """STRICT TALLY PRIME FORMAT: Debit = Yes/-Amount | Credit = No/Amount"""
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
                vch, amt = "Payment", val_dr
                l1_n, l1_p, l1_a = target, "Yes", -amt
                l2_n, l2_p, l2_a = bank_led, "No", amt
            elif val_cr > 0:
                vch, amt = "Receipt", val_cr
                l1_n, l1_p, l1_a = bank_led, "Yes", -amt
                l2_n, l2_p, l2_a = target, "No", amt
            else: continue

            xml_body += f"""<TALLYMESSAGE xmlns:UDF="TallyUDF">
                <VOUCHER VCHTYPE="{vch}" ACTION="Create">
                    <DATE>{dt}</DATE><NARRATION>{nar}</NARRATION><VOUCHERTYPENAME>{vch}</VOUCHERTYPENAME>
                    <ALLLEDGERENTRIES.LIST><LEDGERNAME>{l1_n}</LEDGERNAME><ISDEEMEDPOSITIVE>{l1_p}</ISDEEMEDPOSITIVE><AMOUNT>{l1_a}</AMOUNT></ALLLEDGERENTRIES.LIST>
                    <ALLLEDGERENTRIES.LIST><LEDGERNAME>{l2_n}</LEDGERNAME><ISDEEMEDPOSITIVE>{l2_p}</ISDEEMEDPOSITIVE><AMOUNT>{l2_a}</AMOUNT></ALLLEDGERENTRIES.LIST>
                </VOUCHER></TALLYMESSAGE>"""
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
st.markdown('<div class="hero-container"><h1>Accounting Expert</h1></div>', unsafe_allow_html=True)
st.markdown('<div class="main-content">', unsafe_allow_html=True)

c1, c2 = st.columns([1, 1.5], gap="large")

with c1:
    st.markdown("### 🛠️ 1. Settings")
    master = st.file_uploader("Upload Tally Master (HTML)", type=['html'])
    synced, options = [], ["Upload Master first"]
    if master:
        synced = extract_ledger_names(master)
        st.toast(f"✅ {len(synced)} Ledgers Synced Successfully!") # POPUP ✅
        options = ["⭐ Auto-Select Bank"] + synced
    bank_choice = st.selectbox("Select Bank Ledger", options)

with c2:
    st.markdown("### 📂 2. Convert & Preview")
    bank_file = st.file_uploader("Upload BOB Statement (Excel)", type=['xlsx', 'xls'])
    
    if bank_file and master:
        df = load_data(bank_file)
        if df is not None:
            # 1. AUTO-BANK DETECTION BOX (Show Below Upload File)
            active_bank = bank_choice
            meta = str(df.iloc[:10].values).upper()
            if "BOB" in meta or "138" in meta:
                active_bank = next((l for l in synced if any(k in l.upper() for k in ["BOB", "BARODA", "138"])), bank_choice)
            
            st.markdown(f'<div class="bank-detect-box">🏦 Selected Bank Account: <b>{active_bank}</b></div>', unsafe_allow_html=True)

            # 2. DATA PREVIEW TABLE
            st.markdown("### 📋 Smart Mapping Preview")
            n_c = next((c for c in df.columns if 'NARRATION' in str(c)), df.columns[1])
            preview_rows = [{"Narration": str(row[n_c])[:50], "Tally Target": trace_identity_power(row[n_c], synced)[0]} for _, row in df.head(10).iterrows()]
            st.table(preview_rows)

            unmatched_upi = [idx for idx, r in df.iterrows() if trace_identity_power(r[n_c], synced)[1] == "⚠️ UPI Alert"]
            
            if len(unmatched_upi) > 5:
                st.markdown(f'<div class="warning-box">⚠️ {len(unmatched_upi)} unknown UPI entries. Select a ledger to continue:</div>', unsafe_allow_html=True)
                upi_fix = st.selectbox("Assign unknown UPIs to:", synced)
                if st.button("🚀 Process & Create Tally XML"):
                    xml_data = generate_tally_xml(df, active_bank, synced, upi_fix)
                    st.balloons()
                    st.download_button("⬇️ Download tally_import.xml", xml_data, file_name="tally_import.xml")
            else:
                if st.button("🚀 Convert to Tally XML"):
                    xml_data = generate_tally_xml(df, active_bank, synced)
                    st.balloons()
                    st.download_button("⬇️ Download tally_import.xml", xml_data, file_name="tally_import.xml")

st.markdown('</div>', unsafe_allow_html=True)

# --- 5. SLIM PINNED FOOTER ---
s_logo = get_img_as_base64("logo 1.png")
s_html = f'<img src="data:image/png;base64,{s_logo}" width="20" style="vertical-align:middle; margin-right:5px;">' if s_logo else ""
st.markdown(f"""
    <div class="footer">
        Sponsored By {s_html} <b>Uday Mondal</b> (Advocate) | Created by <b>Debasish Biswas</b>
    </div>
""", unsafe_allow_html=True)
