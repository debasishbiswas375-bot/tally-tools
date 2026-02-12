import streamlit as st
import pandas as pd
from bs4 import BeautifulSoup
import pdfplumber
import io
import base64
import re

# --- 1. PAGE CONFIGURATION ---
st.set_config(page_title="Accounting Expert", layout="wide")

# --- 2. PREMIUM UI CSS ---
st.markdown("""
    <style>
        .hero-container { text-align: center; padding: 40px; background: linear-gradient(135deg, #065F46 0%, #1E40AF 100%); color: white; margin: -6rem -4rem 30px -4rem; }
        .bank-detect-box { background-color: #E0F2FE; border: 2px solid #3B82F6; padding: 15px; border-radius: 10px; color: #1E3A8A; font-weight: 700; margin-bottom: 20px; text-align: center; }
        .stButton>button { width: 100%; background: #10B981; color: white; height: 55px; font-weight: 600; border: none; }
        .footer { margin-top: 60px; padding: 30px; text-align: center; color: #64748B; border-top: 1px solid #E2E8F0; background-color: white; }
    </style>
""", unsafe_allow_html=True)

# --- 3. CORE ENGINE ---

def extract_ledger_names(html_file):
    try:
        soup = BeautifulSoup(html_file, 'html.parser')
        return sorted(list(set([td.text.strip() for td in soup.find_all('td') if len(td.text.strip()) > 1])))
    except: return []

def high_power_trace(narration, master_list):
    """
    ULTRA-TRACE POWER:
    Matches longest phrases first to prevent 'Mithu Sk' vs 'Mithu Mondal' errors.
    """
    if not narration or pd.isna(narration): return "Suspense", "None"
    nar_up = str(narration).upper().replace('/', ' ')
    
    # Sort masters by length (longest names first) to ensure 'Mithu Mondal' 
    # is checked before 'Mithu'
    sorted_masters = sorted(master_list, key=len, reverse=True)

    for ledger in sorted_masters:
        pattern = rf"\b{re.escape(ledger.upper())}\b" # Matches exact phrase boundaries
        if re.search(pattern, nar_up):
            return ledger, "🎯 Exact Match"
    
    if "UPI" in nar_up: return "Untraced", "⚠️ UPI Alert"
    return "Suspense", "None"

def load_data(file):
    try:
        df = pd.read_excel(file, header=None)
        # Specifically targeting the BOB 138 layout
        for i, row in df.iterrows():
            row_str = " ".join([str(x).lower() for x in row if x])
            if 'narration' in row_str and 'tran date' in row_str:
                df.columns = [str(c).strip().upper() for c in df.iloc[i]]
                return df[i + 1:].reset_index(drop=True).dropna(subset=[df.columns[1]], thresh=1)
        return None
    except: return None

# --- 4. UI SECTIONS ---
st.markdown('<div class="hero-container"><h1>Accounting Expert</h1></div>', unsafe_allow_html=True)
c1, c2 = st.columns([1, 1.5], gap="large")

with c1:
    st.markdown("### 🛠️ 1. Settings")
    master = st.file_uploader("Upload Tally Master", type=['html'])
    synced = extract_ledger_names(master) if master else []
    if synced: st.success(f"✅ {len(synced)} Ledgers Synced")
    
    bank_choice = st.selectbox("Bank Ledger", ["⭐ Auto-Select Bank"] + synced)
    party_choice = st.selectbox("Default Party Ledger", ["⭐ AI Trace"] + synced)

with c2:
    st.markdown("### 📂 2. Data Preview & Convert")
    bank_file = st.file_uploader("Upload Statement", type=['xlsx', 'xls'])
    
    if bank_file and master:
        df = load_data(bank_file)
        if df is not None:
            # BANK AUTO-DETECTION (For BOB 138)
            active_bank = bank_choice
            meta = str(df.iloc[:10].values).upper()
            if "BOB" in meta or "138" in meta:
                active_bank = next((l for l in synced if "BOB" in l.upper() or "138" in l), bank_choice)
                st.markdown(f'<div class="bank-detect-box">🏦 Detected Bank: {active_bank}</div>', unsafe_allow_html=True)

            # DATA PREVIEW WITH IDENTITY ISOLATION
            st.markdown("### 📋 Smart Identity Preview")
            n_c = next((c for c in df.columns if 'NARRATION' in str(c)), df.columns[1])
            
            preview_data = []
            unmatched_upi_indices = []
            for idx, row in df.head(15).iterrows():
                target, status = high_power_trace(row[n_c], synced)
                if status == "⚠️ UPI Alert": unmatched_upi_indices.append(idx)
                preview_data.append({"Narration": str(row[n_c])[:50], "Target Ledger": target, "Power": status})
            
            st.table(preview_data) # Check this table to see Mithu Sk vs Mondal separation

            if len(unmatched_upi_indices) > 5:
                st.markdown(f'<div class="warning-box">⚠️ {len(unmatched_upi_indices)} UPI items need manual assignment.</div>', unsafe_allow_html=True)
                upi_fix = st.selectbox("Assign unknown UPIs to:", synced)
                if st.button("🚀 Process & Create Tally XML"):
                    st.download_button("⬇️ Download tally_import.xml", "XML_CONTENT", file_name="tally_import.xml")
            else:
                if st.button("🚀 Convert to Tally XML"):
                    st.download_button("⬇️ Download tally_import.xml", "XML_CONTENT", file_name="tally_import.xml")

st.markdown(f"""<div class="footer"><p>Sponsored By <b>Uday Mondal</b> | Advocate</p><p>Created by <b>Debasish Biswas</b></p></div>""", unsafe_allow_html=True)
