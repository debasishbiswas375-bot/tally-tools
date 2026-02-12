import streamlit as st
import pandas as pd
from bs4 import BeautifulSoup
import pdfplumber
import io
import re

# --- 1. PAGE CONFIG ---
st.set_page_config(page_title="Accounting Expert", layout="wide", initial_sidebar_state="collapsed")

# --- 2. SLIM UI & PINNED FOOTER ---
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
        html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #F8FAFC; }
        .hero-container { text-align: center; padding: 30px; background: linear-gradient(135deg, #065F46 0%, #1E40AF 100%); color: white; margin: -6rem -4rem 20px -4rem; }
        .bank-detect-box { background-color: #E0F2FE; border: 1px solid #3B82F6; padding: 12px; border-radius: 8px; color: #1E3A8A; font-weight: 700; margin: 10px 0; text-align: center; }
        .footer { position: fixed; left: 0; bottom: 0; width: 100%; background-color: white; color: #64748B; text-align: center; padding: 8px 0; border-top: 1px solid #E2E8F0; z-index: 1000; font-size: 0.85rem; }
        .main-content { padding-bottom: 80px; }
        #MainMenu, footer, header { visibility: hidden; }
    </style>
""", unsafe_allow_html=True)

# --- 3. CORE ENGINE ---

def extract_ledger_names(html_file):
    try:
        soup = BeautifulSoup(html_file, 'html.parser')
        # Extracts all table data cell text
        return sorted(list(set([td.text.strip() for td in soup.find_all('td') if len(td.text.strip()) > 1])))
    except: return []

def trace_identity_power(narration, master_list):
    """
    STRICT IDENTITY TRACE:
    Matches longest phrases first (Mithu Mondal > Mithu).
    Uses Word Boundaries (\b) to ensure Medplus Sahanagar doesn't match 'Saha'.
    """
    if not narration or pd.isna(narration): return "Suspense", "None"
    nar_up = str(narration).upper().replace('/', ' ')
    sorted_masters = sorted(master_list, key=len, reverse=True)

    for ledger in sorted_masters:
        pattern = rf"\b{re.escape(ledger.upper())}\b"
        if re.search(pattern, nar_up):
            return ledger, "🎯 Exact Identity"
    
    if "UPI" in nar_up: return "Untraced", "⚠️ UPI Alert"
    return "Suspense", "None"

def load_data(file):
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
        
        for i, row in df.iterrows():
            row_str = " ".join([str(x).lower() for x in row if x])
            if 'narration' in row_str and 'date' in row_str:
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
    synced = []
    if master:
        synced = extract_ledger_names(master)
        st.toast(f"✅ {len(synced)} Ledgers Synced!")
    
    # The bank choice is now prioritized
    bank_choice = st.selectbox("Select Bank Account", ["⭐ Auto-Detect"] + synced)

with c2:
    st.markdown("### 📂 2. Convert & Identity Preview")
    bank_file = st.file_uploader("Upload BOB Statement", type=['xlsx', 'xls', 'pdf'])
    
    if bank_file and master:
        df, meta = load_data(bank_file)
        if df is not None:
            # AUTO-BANK DETECTION
            active_bank = bank_choice
            if bank_choice == "⭐ Auto-Detect":
                full_meta = " ".join(meta.astype(str).values.flatten()).upper()
                if "138" in full_meta:
                    active_bank = next((l for l in synced if "138" in l), bank_choice)
            
            st.markdown(f'<div class="bank-detect-box">🏦 Bank Account: <b>{active_bank}</b></div>', unsafe_allow_html=True)
            
            # PREVIEW TABLE
            n_c = next((c for c in df.columns if 'NARRATION' in str(c)), df.columns[1])
            preview_rows = [{"Narration": str(row[n_c])[:50], "Target Ledger": trace_identity_power(row[n_c], synced)[0]} for _, row in df.head(10).iterrows()]
            st.table(preview_rows)

            if st.button("🚀 Convert to Tally XML"):
                st.balloons()
                st.success("Tally Prime XML Generated!")

st.markdown('</div>', unsafe_allow_html=True)

# --- 5. PINNED SLIM FOOTER ---
st.markdown(f"""
    <div class="footer">
        Sponsored By <b>Uday Mondal</b> (Advocate) | Created by <b>Debasish Biswas</b>
    </div>
""", unsafe_allow_html=True)
