import streamlit as st
import pandas as pd
from bs4 import BeautifulSoup
import pdfplumber
import io
import base64

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(page_title="Accounting Expert", layout="wide", initial_sidebar_state="collapsed")

# --- 2. PREMIUM UI CSS ---
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
        html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #F8FAFC; }
        .hero-container { text-align: center; padding: 40px; background: linear-gradient(135deg, #065F46 0%, #1E40AF 100%); color: white; margin: -6rem -4rem 30px -4rem; }
        .bank-detect-box { background-color: #E0F2FE; border: 2px solid #3B82F6; padding: 15px; border-radius: 10px; color: #1E3A8A; font-weight: 700; margin-bottom: 20px; text-align: center; }
        .warning-box { background-color: #FEF2F2; border: 2px solid #EF4444; padding: 20px; border-radius: 12px; margin: 20px 0; }
        .stButton>button { width: 100%; background: #10B981; color: white; height: 55px; font-weight: 600; border-radius: 8px; border: none; }
        .footer { margin-top: 60px; padding: 40px; text-align: center; color: #64748B; border-top: 1px solid #E2E8F0; background-color: white; margin-left: -4rem; margin-right: -4rem; }
    </style>
""", unsafe_allow_html=True)

# --- 3. CORE ENGINE ---

def extract_ledger_names(html_file):
    try:
        soup = BeautifulSoup(html_file, 'html.parser')
        return sorted(list(set([td.text.strip() for td in soup.find_all('td') if len(td.text.strip()) > 1])))
    except: return []

def trace_ledger_priority(narration, master_list):
    """Priority 1: Master List | Priority 2: UPI Unmatched."""
    if not narration or pd.isna(narration): return "Suspense", "None"
    nar_up = str(narration).upper()
    for ledger in master_list:
        if ledger.upper() in nar_up: return ledger, "Matched"
    if "UPI" in nar_up: return "Untraced", "UPI_Alert"
    return "Suspense", "None"

def load_data(file):
    """Handles metadata and duplicates."""
    try:
        df = pd.read_excel(file, header=None) if not file.name.endswith('.pdf') else None
        header_idx = 0
        for i, row in df.iterrows():
            row_str = " ".join([str(x).lower() for x in row if x])
            if 'date' in row_str and 'narration' in row_str:
                header_idx = i
                break
        df.columns = [str(c).strip().upper() if not pd.isna(c) else f"COL_{j}" for j, c in enumerate(df.iloc[header_idx])]
        df = df[header_idx + 1:].reset_index(drop=True)
        return df.dropna(subset=[df.columns[1]], thresh=1)
    except: return None

# --- 4. UI SECTIONS ---
st.markdown('<div class="hero-container"><h1>Accounting Expert</h1></div>', unsafe_allow_html=True)
c1, c2 = st.columns([1, 1.5], gap="large")

with c1:
    st.markdown("### 🛠️ 1. Settings")
    master = st.file_uploader("Upload Tally Master", type=['html'])
    synced, options = [], ["Upload Master first"]
    if master:
        synced = extract_ledger_names(master)
        st.success(f"✅ Synced {len(synced)} ledgers")
        options = ["⭐ Auto-Select Bank"] + synced
    bank_choice = st.selectbox("Bank Ledger", options)
    party_choice = st.selectbox("Party Ledger", ["⭐ AI Auto-Trace"] + synced)

with c2:
    st.markdown("### 📂 2. Convert")
    bank_file = st.file_uploader("Drop Statement here", type=['xlsx', 'xls', 'pdf'])
    if bank_file and master:
        df = load_data(bank_file)
        if df is not None:
            # 1. AUTO-BANK DETECTION
            active_bank = bank_choice
            meta = " ".join(df.head(15).astype(str).values.flatten()).upper()
            if (bank_choice == "⭐ Auto-Select Bank") and any(k in meta for k in ["BOB", "BARODA", "138"]):
                active_bank = next((l for l in synced if any(k in l.upper() for k in ["BOB", "BARODA", "138"])), bank_choice)
                st.markdown(f'<div class="bank-detect-box">🏦 Auto-Detected: {active_bank}</div>', unsafe_allow_html=True)

            # 2. UPI VALIDATION
            n_c = next((c for c in df.columns if 'NARRATION' in str(c)), df.columns[1])
            unmatched_upi = [idx for idx, row in df.iterrows() if trace_ledger_priority(row[n_c], synced)[1] == "UPI_Alert"]
            
            if len(unmatched_upi) > 5:
                st.markdown(f'<div class="warning-box">⚠️ {len(unmatched_upi)} UPI transactions not in Master. Please select:</div>', unsafe_allow_html=True)
                upi_fix = st.selectbox("Assign unmatched UPIs to:", synced)
                if st.button("🚀 Process & Preview"):
                    # PREVIEW OF ACTUAL NAMES
                    preview = [{"Narration": str(df.loc[i, n_col])[:50], "Tally Ledger": upi_fix} for i in unmatched_upi[:5]]
                    st.table(preview)
                    st.download_button("⬇️ Download XML", "XML_DATA", file_name="tally_import.xml")
            else:
                if st.button("🚀 Convert & Preview"):
                    preview = [{"Narration": str(row[n_c])[:50], "Tally Ledger": trace_ledger_priority(row[n_c], synced)[0]} for _, row in df.head(5).iterrows()]
                    st.table(preview) # REAL NAMES PREVIEW
                    st.download_button("⬇️ Download XML", "XML_DATA", file_name="tally_import.xml")

st.markdown("""<div class="footer"><p>Sponsored By <b>Uday Mondal</b> | Created by <b>Debasish Biswas</b></p></div>""", unsafe_allow_html=True)
