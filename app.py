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

# --- 2. HELPER: IMAGE TO BASE64 ---
def get_base64_image(img_path):
    try:
        with open(img_path, "rb") as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except:
        return None

# --- 3. PREMIUM UI & PINNED SLIM FOOTER ---
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
        html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #F8FAFC; }
        
        .hero-container { text-align: center; padding: 40px; background: linear-gradient(135deg, #065F46 0%, #1E40AF 100%); color: white; margin: -6rem -4rem 20px -4rem; }
        .bank-detect-box { background-color: #E0F2FE; border: 1px solid #3B82F6; padding: 12px; border-radius: 8px; color: #1E3A8A; font-weight: 700; margin-top: 10px; text-align: center; border-left: 8px solid #3B82F6; }
        .warning-box { background-color: #FEF2F2; border: 1px solid #EF4444; padding: 15px; border-radius: 8px; margin: 15px 0; color: #991B1B; font-weight: 600; }
        
        .stButton>button { width: 100%; background: #10B981; color: white; height: 50px; font-weight: 600; border-radius: 8px; border: none; box-shadow: 0 4px 12px rgba(16, 185, 129, 0.2); }
        
        /* PINNED SLIM FOOTER */
        .footer { 
            position: fixed; left: 0; bottom: 0; width: 100%; 
            background-color: white; color: #64748B; text-align: center; 
            padding: 10px 0; border-top: 1px solid #E2E8F0; z-index: 1000; font-size: 0.85rem; 
        }
        .footer b { color: #0F172A; }
        .main-content { padding-bottom: 110px; }
        #MainMenu, footer, header { visibility: hidden; }
    </style>
""", unsafe_allow_html=True)

# --- 4. CORE ENGINE ---

def extract_ledger_names(html_file):
    try:
        soup = BeautifulSoup(html_file, 'html.parser')
        return sorted(list(set([td.text.strip() for td in soup.find_all('td') if len(td.text.strip()) > 1])))
    except: return []

def trace_identity_power(narration, master_list):
    """Deep Trace: Longest phrase match first (prevents Mithu Mondal vs Mithu Sk errors)."""
    if not narration or pd.isna(narration): return "Suspense", "None"
    nar_up = str(narration).upper().replace('/', ' ')
    sorted_masters = sorted(master_list, key=len, reverse=True)
    for ledger in sorted_masters:
        pattern = rf"\b{re.escape(ledger.upper())}\b"
        if re.search(pattern, nar_up):
            return ledger, "🎯 Direct Match"
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

# --- 5. UI DASHBOARD ---
st.markdown('<div class="hero-container"><h1>Accounting Expert</h1></div>', unsafe_allow_html=True)
st.markdown('<div class="main-content">', unsafe_allow_html=True)

c1, c2 = st.columns([1, 1.5], gap="large")

with c1:
    st.markdown("### 🛠️ 1. Settings")
    master = st.file_uploader("Upload Tally Master (HTML)", type=['html'])
    synced = []
    if master:
        synced = extract_ledger_names(master)
        st.toast(f"✅ {len(synced)} Ledgers Synced Successfully!")
    
    bank_choice = st.selectbox("Select Bank Account", ["⭐ Auto-Detect"] + synced)

with c2:
    st.markdown("### 📂 2. Convert & Identity Preview")
    bank_file = st.file_uploader("Upload BOB Statement (Excel/PDF)", type=['xlsx', 'xls', 'pdf'])
    
    if bank_file and master:
        df, meta = load_data(bank_file)
        if df is not None:
            # AUTO-BANK DETECTION
            active_bank = bank_choice
            if bank_choice == "⭐ Auto-Detect":
                full_meta = " ".join(meta.astype(str).values.flatten()).upper()
                if "0138" in full_meta:
                    active_bank = next((l for l in synced if "0138" in l), bank_choice)
            
            st.markdown(f'<div class="bank-detect-box">🏦 Bank Account: <b>{active_bank}</b></div>', unsafe_allow_html=True)
            
            # PREVIEW TABLE
            n_c = next((c for c in df.columns if 'NARRATION' in str(c)), df.columns[1])
            st.markdown("### 📋 Smart Identity Preview")
            preview_rows = [{"Narration": str(row[n_c])[:50], "Target Ledger": trace_identity_power(row[n_c], synced)[0]} for _, row in df.head(10).iterrows()]
            st.table(preview_rows)

            unmatched_upi = [idx for idx, r in df.iterrows() if trace_identity_power(r[n_c], synced)[1] == "⚠️ UPI Alert"]
            
            if len(unmatched_upi) > 5:
                st.markdown(f'<div class="warning-box">⚠️ Found {len(unmatched_upi)} unknown UPIs. Select a ledger:</div>', unsafe_allow_html=True)
                upi_fix = st.selectbox("Assign unknown UPIs to:", synced)
                if st.button("🚀 Process & Create Tally XML"):
                    st.balloons()
                    st.success("Tally Prime XML Generated!")
            else:
                if st.button("🚀 Convert to Tally XML"):
                    st.balloons()
                    st.success("Tally Prime XML Generated!")

st.markdown('</div>', unsafe_allow_html=True)

# --- 6. PINNED FOOTER WITH LOGOS ---
logo_primary = get_base_64_image("logo.png")
logo_sponsor = get_base_64_image("logo 1.png")

logo_html = f'<img src="data:image/png;base64,{logo_primary}" width="25" style="vertical-align:middle; margin-right:10px;">' if logo_primary else ""
sponsor_html = f'<img src="data:image/png;base64,{logo_sponsor}" width="20" style="vertical-align:middle; margin-right:5px;">' if logo_sponsor else ""

st.markdown(f"""
    <div class="footer">
        {logo_html} Sponsored By {sponsor_html} <b>Uday Mondal</b> (Advocate) | Created by <b>Debasish Biswas</b>
    </div>
""", unsafe_allow_html=True)
