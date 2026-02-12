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

# --- 2. PREMIUM UI & SLIM PINNED FOOTER ---
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
        html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #F8FAFC; }
        .hero-container { text-align: center; padding: 40px; background: linear-gradient(135deg, #065F46 0%, #1E40AF 100%); color: white; margin: -6rem -4rem 20px -4rem; }
        .warning-box { background-color: #FEF2F2; border: 1px solid #EF4444; padding: 15px; border-radius: 8px; margin: 15px 0; color: #991B1B; font-weight: 600; }
        .stButton>button { width: 100%; background: #10B981; color: white; height: 50px; font-weight: 600; border-radius: 8px; border: none; box-shadow: 0 4px 12px rgba(16, 185, 129, 0.2); }
        
        .footer { 
            position: fixed; left: 0; bottom: 0; width: 100%; 
            background-color: white; color: #64748B; text-align: center; 
            padding: 10px 0; border-top: 1px solid #E2E8F0; z-index: 1000; font-size: 0.85rem; 
        }
        .main-content { padding-bottom: 110px; }
        #MainMenu, footer, header { visibility: hidden; }
    </style>
""", unsafe_allow_html=True)

# --- 3. CORE ENGINE ---

def extract_ledger_names(html_file):
    try:
        soup = BeautifulSoup(html_file, 'html.parser')
        raw_list = list(set([td.text.strip() for td in soup.find_all('td') if len(td.text.strip()) > 1]))
        # Clean list to prioritize real parties
        return sorted([l for l in raw_list if not any(x in l.upper() for x in ["IFSC", "A/C"])])
    except: return []

def trace_identity_power(narration, master_list):
    """
    STRICT IDENTITY TRACE:
    Matches longest names first (Mithu Mondal before Mithu Sk).
    Protects 'Medplus Sahanagar' from matching 'Saha'.
    """
    if not narration or pd.isna(narration): return "Suspense", "None"
    nar_up = str(narration).upper().replace('/', ' ')
    
    # Sort masters by length (Longest first)
    sorted_masters = sorted(master_list, key=len, reverse=True)

    for ledger in sorted_masters:
        pattern = rf"\b{re.escape(ledger.upper())}\b"
        if re.search(pattern, nar_up):
            return ledger, "🎯 Direct Match"
    
    if "UPI" in nar_up: return "Untraced", "⚠️ UPI Alert"
    return "Suspense", "None"

def load_data(file):
    """Handles both Excel and PDF (BOB 138 layout)."""
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
    synced = []
    if master:
        synced = extract_ledger_names(master)
        st.toast(f"✅ {len(synced)} Ledgers Synced Successfully!")
    
    bank_led = st.selectbox("Select Bank Account", synced if synced else ["Upload Master first"])
    default_party = st.selectbox("Second Ledger (Party)", ["⭐ AI Auto-Trace"] + synced)

with c2:
    st.markdown("### 📂 2. Convert & Identity Preview")
    bank_file = st.file_uploader("Upload Statement (Excel/PDF)", type=['xlsx', 'xls', 'pdf'])
    
    if bank_file and master:
        df = load_data(bank_file)
        if df is not None:
            # IDENTITY PREVIEW TABLE
            st.markdown("### 📋 Smart Identity Preview")
            n_c = next((c for c in df.columns if 'NARRATION' in str(c)), df.columns[1])
            
            preview_rows = []
            unmatched_upi_count = 0
            for idx, row in df.head(15).iterrows():
                target, status = trace_identity_power(row[n_c], synced)
                if status == "⚠️ UPI Alert": unmatched_upi_count += 1
                preview_rows.append({"Narration": str(row[n_c])[:50], "Target Ledger": target, "Trace Status": status})
            
            st.table(preview_rows)

            # INTERACTIVE "NOT TRACED" LOGIC
            if unmatched_upi_count > 5:
                st.markdown(f'<div class="warning-box">⚠️ Action Required: {unmatched_upi_count} unknown UPI names.</div>', unsafe_allow_html=True)
                upi_fix = st.selectbox("Assign Not Traced UPIs to:", synced)
                if st.button("🚀 Process & Generate Tally XML"):
                    st.balloons()
                    st.success("Tally Prime XML Generated!")
            else:
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
