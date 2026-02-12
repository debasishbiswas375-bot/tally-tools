import streamlit as st
import pandas as pd
from bs4 import BeautifulSoup
import pdfplumber
from difflib import get_close_matches
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
        .stButton>button { width: 100%; background: #10B981; color: white; height: 55px; font-weight: 600; border-radius: 8px; border: none; }
        .footer { margin-top: 60px; padding: 40px; text-align: center; color: #64748B; border-top: 1px solid #E2E8F0; background-color: white; margin-left: -4rem; margin-right: -4rem; }
    </style>
""", unsafe_allow_html=True)

# --- 3. HIGH-POWER TRACE ENGINE ---

def extract_ledger_names(html_file):
    try:
        soup = BeautifulSoup(html_file, 'html.parser')
        return sorted(list(set([td.text.strip() for td in soup.find_all('td') if len(td.text.strip()) > 1])))
    except: return []

def advanced_trace(narration, master_list):
    """Enhanced Trace Power: Exact Match -> Partial Match -> UPI Check."""
    if not narration or pd.isna(narration): return "Suspense", "None"
    nar_up = str(narration).upper()
    
    # Level 1: Strict Exact Match
    for ledger in master_list:
        if ledger.upper() in nar_up:
            return ledger, "🎯 Direct Match"
            
    # Level 2: Fuzzy Matching (High Trace Power)
    # Extracts words from narration and checks similarity to ledgers
    words = nar_up.replace('/', ' ').split()
    for word in words:
        if len(word) < 4: continue
        matches = get_close_matches(word, master_list, n=1, cutoff=0.8)
        if matches:
            return matches[0], "⚡ Fuzzy Match"

    if "UPI" in nar_up: return "Untraced", "⚠️ UPI Alert"
    return "Suspense", "None"

def load_data(file):
    try:
        df = pd.read_excel(file, header=None) if not file.name.endswith('.pdf') else None
        # Locate header for BOB 138
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

# --- 4. UI DASHBOARD ---
st.markdown('<div class="hero-container"><h1>Accounting Expert</h1><p>High-Power AI Trace Engine</p></div>', unsafe_allow_html=True)
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
    bank_file = st.file_uploader("Upload Bank Statement", type=['xlsx', 'xls', 'pdf'])
    
    if bank_file and master:
        df = load_data(bank_file)
        if df is not None:
            # AUTO-BANK DETECTION
            active_bank = bank_choice
            meta = " ".join(df.head(15).astype(str).values.flatten()).upper()
            if "BOB" in meta or "138" in meta:
                active_bank = next((l for l in synced if "BOB" in l.upper() or "138" in l), bank_choice)
                st.markdown(f'<div class="bank-detect-box">🏦 Auto-Detected: {active_bank}</div>', unsafe_allow_html=True)

            # --- THE DATA PREVIEW (REAL-TIME TRACING) ---
            st.markdown("### 📋 Smart Data Preview")
            n_c = next((c for c in df.columns if 'NARRATION' in str(c)), df.columns[1])
            
            preview_data = []
            unmatched_upi_count = 0
            for idx, row in df.head(15).iterrows():
                target, status = advanced_trace(row[n_c], synced)
                if status == "⚠️ UPI Alert": unmatched_upi_count += 1
                preview_data.append({"Statement Narration": str(row[n_c])[:60], "Tally Target": target, "Trace Power": status})
            
            st.table(preview_data)

            # INTERACTIVE UPI BLOCK
            if unmatched_upi_count > 5:
                st.error(f"🚨 {unmatched_upi_count} UPI transactions found without Master matches.")
                upi_fix = st.selectbox("Assign these UPIs to:", synced)
                if st.button("🚀 Finalize XML"):
                    st.download_button("⬇️ Download tally_import.xml", "XML_DATA", file_name="tally_import.xml")
            else:
                if st.button("🚀 Convert to Tally XML"):
                    st.download_button("⬇️ Download tally_import.xml", "XML_DATA", file_name="tally_import.xml")

# --- 5. FOOTER ---
st.markdown(f"""<div class="footer"><p>Sponsored By <b>Uday Mondal</b> | Advocate</p><p>Created by <b>Debasish Biswas</b></p></div>""", unsafe_allow_html=True)
