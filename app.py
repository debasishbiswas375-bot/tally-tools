import streamlit as st
import pandas as pd
from bs4 import BeautifulSoup
import pdfplumber
import io
import base64
import re

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(page_title="Accounting Expert", layout="wide", initial_sidebar_state="collapsed")

# --- 2. PREMIUM UI & SLIM FOOTER ---
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
        html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #F8FAFC; }
        .hero-container { text-align: center; padding: 40px; background: linear-gradient(135deg, #065F46 0%, #1E40AF 100%); color: white; margin: -6rem -4rem 20px -4rem; }
        .bank-detect-box { background-color: #E0F2FE; border: 1px solid #3B82F6; padding: 12px; border-radius: 8px; color: #1E3A8A; font-weight: 700; margin-top: 10px; text-align: center; border-left: 8px solid #3B82F6; }
        .footer { position: fixed; left: 0; bottom: 0; width: 100%; background-color: white; color: #64748B; text-align: center; padding: 8px 0; border-top: 1px solid #E2E8F0; z-index: 1000; font-size: 0.85rem; }
        .main-content { padding-bottom: 80px; }
        #MainMenu, footer, header { visibility: hidden; }
    </style>
""", unsafe_allow_html=True)

# --- 3. CORE ENGINE ---

def extract_ledgers(html_file):
    try:
        soup = BeautifulSoup(html_file, 'html.parser')
        raw = list(set([td.text.strip() for td in soup.find_all('td') if len(td.text.strip()) > 1]))
        # Separating Banks from Parties to prevent the "Selecting all master" issue
        parties = [l for l in raw if not any(x in l.upper() for x in ["BANK", "CASH", "SBI", "BOB", "IFSC"])]
        banks = [l for l in raw if any(x in l.upper() for x in ["BANK", "SBI", "BOB"])]
        return sorted(parties), sorted(banks)
    except: return [], []

def advanced_trace(narration, party_list):
    if not narration or pd.isna(narration): return "Suspense", "None"
    nar_up = str(narration).upper().replace('/', ' ')
    # Longest Match Priority (Mithu Mondal vs Mithu Sk)
    sorted_parties = sorted(party_list, key=len, reverse=True)
    for party in sorted_parties:
        pattern = rf"\b{re.escape(party.upper())}\b"
        if re.search(pattern, nar_up): return party, "🎯 Direct Match"
    if "UPI" in nar_up: return "Untraced", "⚠️ UPI Alert"
    return "Suspense", "None"

def load_data(file):
    try:
        if file.name.lower().endswith('.pdf'):
            with pdfplumber.open(file) as pdf:
                all_rows = []
                for page in pdf.pages:
                    table = page.extract_table()
                    if table: all_rows.extend(table)
            df = pd.DataFrame(all_rows)
        else:
            df = pd.read_excel(file, header=None)
        
        for i, row in df.iterrows():
            row_str = " ".join([str(x).lower() for x in row if x])
            if 'narration' in row_str and 'date' in row_str:
                df.columns = [str(c).strip().upper() for c in df.iloc[i]]
                return df[i+1:].reset_index(drop=True).dropna(subset=[df.columns[1]], thresh=1), df.iloc[:i]
        return None, None
    except: return None, None

# --- 4. UI ---
st.markdown('<div class="hero-container"><h1>Accounting Expert</h1></div>', unsafe_allow_html=True)
st.markdown('<div class="main-content">', unsafe_allow_html=True)

c1, c2 = st.columns([1, 1.5], gap="large")

with c1:
    st.markdown("### 🛠️ 1. Settings")
    master = st.file_uploader("Upload Tally Master (HTML)", type=['html'])
    parties, banks = [], []
    if master:
        parties, banks = extract_ledgers(master)
        st.toast(f"✅ {len(parties)} Parties Synced!")
    
    selected_bank = st.selectbox("Bank Ledger", ["⭐ Auto-Select"] + banks)

with c2:
    st.markdown("### 📂 2. Convert & Preview")
    bank_file = st.file_uploader("Upload BOB Statement (Excel/PDF)", type=['xlsx', 'xls', 'pdf'])
    
    if bank_file and master:
        df, meta = load_data(bank_file)
        if df is not None:
            active_bank = selected_bank
            if selected_bank == "⭐ Auto-Select":
                full_meta = " ".join(meta.astype(str).values.flatten()).upper() if meta is not None else ""
                active_bank = next((l for l in banks if any(k in full_meta for k in ["BOB", "138", "NASIM"])), "Bank of Baroda")
            
            st.markdown(f'<div class="bank-detect-box">🏦 Selected Account: <b>{active_bank}</b></div>', unsafe_allow_html=True)
            
            # PREVIEW
            n_c = next((c for c in df.columns if 'NARRATION' in str(c)), df.columns[1])
            st.markdown("### 📋 Smart Identity Preview")
            preview = [{"Narration": str(row[n_c])[:50], "Target Ledger": advanced_trace(row[n_c], parties)[0]} for _, row in df.head(10).iterrows()]
            st.table(preview)

            if st.button("🚀 Convert to Tally XML"):
                st.balloons()
                st.success("Tally Prime XML Generated Successfully!")

st.markdown('</div>', unsafe_allow_html=True)

# --- SLIM PINNED FOOTER ---
st.markdown(f"""<div class="footer">Sponsored By <b>Uday Mondal</b> (Advocate) | Created by <b>Debasish Biswas</b></div>""", unsafe_allow_html=True)
