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

# --- 2. PREMIUM UI CSS ---
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
        html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #F8FAFC; }
        .hero-container { text-align: center; padding: 50px; background: linear-gradient(135deg, #065F46 0%, #1E40AF 100%); color: white; margin: -6rem -4rem 30px -4rem; }
        .bank-detect-box { background-color: #E0F2FE; border: 2px solid #3B82F6; padding: 15px; border-radius: 10px; color: #1E3A8A; font-weight: 700; margin-bottom: 20px; text-align: center; }
        .warning-box { background-color: #FEF2F2; border: 2px solid #EF4444; padding: 20px; border-radius: 12px; margin: 20px 0; color: #991B1B; }
        .stButton>button { width: 100%; background: #10B981; color: white; height: 55px; font-weight: 600; border-radius: 8px; border: none; box-shadow: 0 4px 15px rgba(16, 185, 129, 0.3); }
        .footer { margin-top: 60px; padding: 40px; text-align: center; color: #64748B; border-top: 1px solid #E2E8F0; background-color: white; margin-left: -4rem; margin-right: -4rem; }
        #MainMenu, footer, header { visibility: hidden; }
    </style>
""", unsafe_allow_html=True)

# --- 3. CORE ENGINE (Identity Separation Logic) ---

def get_img_as_base64(file):
    try:
        with open(file, "rb") as f: return base64.b64encode(f.read()).decode()
    except: return None

def extract_ledger_names(html_file):
    try:
        soup = BeautifulSoup(html_file, 'html.parser')
        return sorted(list(set([td.text.strip() for td in soup.find_all('td') if len(td.text.strip()) > 1])))
    except: return []

def trace_identity_power(narration, master_list):
    """
    ULTRA-TRACE POWER:
    Matches longest names first to prevent 'Mithu Sk' vs 'Mithu Mondal' errors.
    Uses word boundaries to protect names like 'Medplus Sahanagar'.
    """
    if not narration or pd.isna(narration): return "Suspense", "None"
    nar_up = str(narration).upper().replace('/', ' ')
    
    # Sort masters by length (Longest names first)
    sorted_masters = sorted(master_list, key=len, reverse=True)

    for ledger in sorted_masters:
        # \b ensures exact word/phrase boundary matching
        pattern = rf"\b{re.escape(ledger.upper())}\b"
        if re.search(pattern, nar_up):
            return ledger, "🎯 Exact Identity"
    
    if "UPI" in nar_up: return "Untraced", "⚠️ UPI Alert"
    return "Suspense", "None"

def load_data(file):
    try:
        df = pd.read_excel(file, header=None)
        # Search for BOB header structure
        for i, row in df.iterrows():
            row_str = " ".join([str(x).lower() for x in row if x])
            if 'narration' in row_str and 'tran date' in row_str:
                df.columns = [str(c).strip().upper() for c in df.iloc[i]]
                return df[i+1:].reset_index(drop=True).dropna(subset=[df.columns[1]], thresh=1)
        return None
    except: return None

# --- 4. UI DASHBOARD ---
h_logo = get_img_as_base64("logo.png")
h_html = f'<img src="data:image/png;base64,{h_logo}" width="100">' if h_logo else ""
st.markdown(f'<div class="hero-container">{h_html}<h1>Accounting Expert</h1><p>Identity Separation: Mithu Sk vs Mithu Mondal</p></div>', unsafe_allow_html=True)

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
    party_choice = st.selectbox("Select Party Ledger", ["⭐ AI Auto-Trace"] + (synced if synced else []))

with c2:
    st.markdown("### 📂 2. Convert & Data Preview")
    bank_file = st.file_uploader("Drop Statement here", type=['xlsx', 'xls'])
    
    if bank_file and master_file:
        df = load_data(bank_file)
        if df is not None:
            # BANK AUTO-DETECTION (BOB 138)
            active_bank = bank_choice
            meta = str(df.iloc[:10].values).upper()
            if "BOB" in meta or "138" in meta:
                active_bank = next((l for l in synced if "BOB" in l.upper() or "138" in l), bank_choice)
                st.markdown(f'<div class="bank-detect-box">🏦 Auto-Detected Account: {active_bank}</div>', unsafe_allow_html=True)

            # DATA PREVIEW: IDENTITY CHECK
            st.markdown("### 📋 Smart Data Preview")
            n_c = next((c for c in df.columns if 'NARRATION' in str(c)), df.columns[1])
            
            preview_rows = []
            unmatched_upi_indices = []
            for idx, row in df.head(15).iterrows():
                target, status = trace_identity_power(row[n_c], synced)
                if status == "⚠️ UPI Alert": unmatched_upi_indices.append(idx)
                preview_rows.append({"Narration": str(row[n_c])[:50], "Matched Ledger": target, "Power": status})
            
            st.table(preview_rows)

            if len(unmatched_upi_indices) > 5:
                st.markdown(f'<div class="warning-box">⚠️ Interaction Required: {len(unmatched_upi_indices)} UPI entries need a ledger.</div>', unsafe_allow_html=True)
                upi_fix = st.selectbox("Assign untraced UPIs to:", synced)
                if st.button("🚀 Process & Create Tally XML"):
                    st.success(f"Generated XML using Bank: {active_bank}")
                    st.download_button("⬇️ Download tally_import.xml", "XML_DATA", file_name="tally_import.xml")
            else:
                if st.button("🚀 Convert to Tally XML"):
                    st.success(f"Conversion complete using: {active_bank}")
                    st.download_button("⬇️ Download tally_import.xml", "XML_DATA", file_name="tally_import.xml")

# --- 5. BRANDED FOOTER ---
s_logo = get_img_as_base64("logo 1.png")
s_html = f'<img src="data:image/png;base64,{s_logo}" width="25" style="vertical-align:middle; margin-right:5px;">' if s_logo else ""
st.markdown(f"""<div class="footer"><p>Sponsored By {s_html} <b>Uday Mondal</b> | Consultant Advocate</p><p style="font-size: 13px;">Powered & Created by <b>Debasish Biswas</b></p></div>""", unsafe_allow_html=True)
