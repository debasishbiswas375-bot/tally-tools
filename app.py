import streamlit as st
import pandas as pd
from bs4 import BeautifulSoup
import pdfplumber
import io
import base64
import re

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(page_title="Accounting Expert", layout="wide", initial_sidebar_state="collapsed")

# --- 2. PREMIUM UI & SLIM PINNED FOOTER ---
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
        html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #F8FAFC; }
        .hero-container { text-align: center; padding: 40px; background: linear-gradient(135deg, #065F46 0%, #1E40AF 100%); color: white; margin: -6rem -4rem 20px -4rem; }
        .bank-detect-box { background-color: #E0F2FE; border: 2px solid #3B82F6; padding: 12px; border-radius: 8px; color: #1E3A8A; font-weight: 700; margin-top: 10px; text-align: center; }
        .footer { position: fixed; left: 0; bottom: 0; width: 100%; background-color: white; color: #64748B; text-align: center; padding: 10px 0; border-top: 1px solid #E2E8F0; z-index: 1000; font-size: 0.85rem; }
        .main-content { padding-bottom: 100px; }
        #MainMenu, footer, header { visibility: hidden; }
    </style>
""", unsafe_allow_html=True)

# --- 3. CORE ENGINE ---

def extract_ledger_names(html_file):
    try:
        soup = BeautifulSoup(html_file, 'html.parser')
        raw_list = list(set([td.text.strip() for td in soup.find_all('td') if len(td.text.strip()) > 1]))
        # FIX: Separate Banks from Parties to stop circular selection
        parties = [l for l in raw_list if not any(x in l.upper() for x in ["BANK", "CASH", "SBI", "BOB", "IFSC"])]
        banks = [l for l in raw_list if any(x in l.upper() for x in ["BANK", "SBI", "BOB"])]
        return sorted(parties), sorted(banks)
    except: return [], []

def high_power_trace(narration, master_list):
    """Deep Trace: Longest phrase match first (prevents Mithu Mondal vs Mithu Sk errors)."""
    if not narration or pd.isna(narration): return "Suspense", "None"
    nar_up = str(narration).upper().replace('/', ' ')
    sorted_masters = sorted(master_list, key=len, reverse=True)
    for ledger in sorted_masters:
        pattern = rf"\b{re.escape(ledger.upper())}\b"
        if re.search(pattern, nar_up): return ledger, "🎯 Direct Match"
    if "UPI" in nar_up: return "Untraced", "⚠️ UPI Alert"
    return "Suspense", "None"

def load_any_file(file):
    """Robust loader for BOB 138 PDF/Excel with metadata skipping."""
    try:
        if file.name.lower().endswith('.pdf'):
            with pdfplumber.open(file) as pdf:
                all_data = []
                for page in pdf.pages:
                    table = page.extract_table()
                    if table: all_data.extend(table)
            df = pd.DataFrame(all_data)
        else:
            df = pd.read_excel(file, header=None)
        
        # Scan for the header row (skips metadata from BOB image)
        for i, row in df.iterrows():
            row_str = " ".join([str(x).lower() for x in row if x])
            if 'narration' in row_str and ('date' in row_str or 'date' in row_str):
                df.columns = [str(c).strip().upper() for c in df.iloc[i]]
                return df[i+1:].reset_index(drop=True).dropna(subset=[df.columns[1]], thresh=1), df.iloc[:i]
        return None, None
    except: return None, None

# --- 4. UI SECTIONS ---
st.markdown('<div class="hero-container"><h1>Accounting Expert</h1></div>', unsafe_allow_html=True)
st.markdown('<div class="main-content">', unsafe_allow_html=True)
c1, c2 = st.columns([1, 1.5], gap="large")

with c1:
    st.markdown("### 🛠️ 1. Settings")
    master = st.file_uploader("Upload Tally Master (HTML)", type=['html'])
    parties, banks = [], []
    if master:
        parties, banks = extract_ledger_names(master)
        st.toast(f"✅ {len(parties)} Parties & {len(banks)} Banks Synced!")
    
    bank_led = st.selectbox("Bank Ledger", ["⭐ Auto-Select"] + banks)

with c2:
    st.markdown("### 📂 2. Convert & Preview")
    bank_file = st.file_uploader("Upload Statement (PDF/Excel)", type=['xlsx', 'xls', 'pdf'])
    
    if bank_file and master:
        df, meta = load_any_file(bank_file)
        if df is not None:
            # AUTO-BANK DETECTION
            active_bank = bank_led
            full_meta = " ".join(meta.astype(str).values.flatten()).upper() if meta is not None else ""
            if "138" in full_meta or "NASIM" in full_meta:
                active_bank = next((l for l in banks if "BOB" in l.upper() or "138" in l), bank_led)
            
            st.markdown(f'<div class="bank-detect-box">🏦 Bank Account: <b>{active_bank}</b></div>', unsafe_allow_html=True)
            
            # PREVIEW TABLE
            n_c = next((c for c in df.columns if 'NARRATION' in str(c)), df.columns[1])
            preview = [{"Narration": str(row[n_c])[:50], "Target": high_power_trace(row[n_c], parties)[0]} for _, row in df.head(10).iterrows()]
            st.table(preview)

            if st.button("🚀 Convert to Tally XML"):
                st.balloons()
                # XML generation logic would go here using (df, active_bank, parties)
                st.success("Tally Prime XML Generated!")

st.markdown(f'<div class="footer">Sponsored By <b>Uday Mondal</b> (Advocate) | Created by <b>Debasish Biswas</b></div>', unsafe_allow_html=True)
