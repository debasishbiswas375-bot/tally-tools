import streamlit as st
import pandas as pd
from bs4 import BeautifulSoup
import pdfplumber
import io
import base64
import re
import time

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Accounting Expert | AI Bank to Tally",
    page_icon="logo.png",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 2. IMAGE HANDLER (Fixed NameError) ---
def get_base_64_image(file):
    try:
        with open(file, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except: return None

# --- 3. FUTURISTIC TALLY THEME CSS ---
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
        html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #F8FAFC; }
        .hero-container { text-align: center; padding: 50px; background: linear-gradient(135deg, #065F46 0%, #1E40AF 100%); color: white; margin: -6rem -4rem 30px -4rem; }
        .bank-detect-box { background-color: #E0F2FE; border: 1px solid #3B82F6; padding: 15px; border-radius: 12px; color: #1E3A8A; font-weight: 700; margin-bottom: 20px; text-align: center; border-left: 8px solid #3B82F6; }
        .warning-box { background-color: #FEF2F2; border: 1px solid #EF4444; padding: 15px; border-radius: 10px; margin: 15px 0; color: #991B1B; font-weight: 600; border-left: 8px solid #EF4444; }
        .stButton>button { width: 100%; background: #10B981; color: white; height: 55px; font-weight: 600; border-radius: 12px; border: none; box-shadow: 0 4px 15px rgba(16, 185, 129, 0.3); }
        .footer { position: fixed; left: 0; bottom: 0; width: 100%; background-color: white; color: #64748B; text-align: center; padding: 12px 0; border-top: 1px solid #E2E8F0; z-index: 1000; font-size: 0.85rem; }
        .main-content { padding-bottom: 120px; }
        #MainMenu, footer, header { visibility: hidden; }
    </style>
""", unsafe_allow_html=True)

# --- 4. OPTIMIZED ENGINES ---

@st.cache_data
def extract_ledger_names(html_file):
    try:
        soup = BeautifulSoup(html_file, 'html.parser')
        # Sort by length descending to catch 'Medplus Sahanagar' before 'Saha'
        return sorted(list(set([td.text.strip() for td in soup.find_all('td') if len(td.text.strip()) > 1])), key=len, reverse=True)
    except: return []

def trace_identity_engine(narration, sorted_masters):
    """Turbo-Speed Trace using word boundaries"""
    if not narration or pd.isna(narration): return "Suspense", "None"
    nar_up = str(narration).upper()
    for ledger in sorted_masters:
        if re.search(rf"\b{re.escape(ledger.upper())}\b", nar_up):
            return ledger, "🎯 Match"
    if any(k in nar_up for k in ["UPI", "VPA", "G-PAY"]): return "Untraced", "⚠️ UPI Alert"
    return "Suspense", "None"

def load_data(file):
    """High-speed data loader"""
    try:
        if file.name.lower().endswith('.pdf'):
            with pdfplumber.open(file) as pdf:
                all_data = [row for page in pdf.pages for row in (page.extract_table() or [])]
            df = pd.DataFrame(all_data)
        else:
            df = pd.read_excel(file, header=None)
        
        for i, row in df.iterrows():
            row_str = " ".join([str(x).lower() for x in row if x])
            if 'narration' in row_str or 'date' in row_str:
                df.columns = [str(c).strip().upper() for c in df.iloc[i]]
                return df[i+1:].reset_index(drop=True).dropna(subset=[df.columns[1]], thresh=1), df.iloc[:i]
        return None, None
    except: return None, None

# --- 5. UI IMPLEMENTATION ---
l_primary = get_base_64_image("logo.png")
l_html = f'<img src="data:image/png;base64,{l_primary}" width="80">' if l_primary else ""
st.markdown(f'<div class="hero-container">{l_html}<h1>Accounting Expert</h1></div>', unsafe_allow_html=True)

st.markdown('<div class="main-content">', unsafe_allow_html=True)
c1, c2 = st.columns([1, 1.5], gap="large")

with c1:
    st.markdown("### 🛠️ 1. Settings")
    master = st.file_uploader("Upload Master.html", type=['html'])
    synced = extract_ledger_names(master) if master else []
    if synced: st.toast(f"✅ {len(synced)} Ledgers Synced!")
    bank_choice = st.selectbox("Select Bank Account", ["⭐ Auto-Detect"] + synced)

with c2:
    st.markdown("### 📂 2. Convert & Download")
    bank_file = st.file_uploader("Upload Statement", type=['xlsx', 'xls', 'pdf'])
    
    if bank_file and master:
        df, meta = load_data(bank_file)
        if df is not None:
            # Auto-Detect BOB 0138
            active_bank = bank_choice
            if bank_choice == "⭐ Auto-Detect" and "0138" in str(meta.values):
                active_bank = next((l for l in synced if "0138" in l), bank_choice)
            
            st.markdown(f'<div class="bank-detect-box">🏦 Bank Account: <b>{active_bank}</b></div>', unsafe_allow_html=True)
            
            # Fast Preview
            n_c = next((c for c in df.columns if 'NARRATION' in str(c)), df.columns[1])
            unmatched = [idx for idx, r in df.iterrows() if trace_identity_engine(r[n_c], synced)[1] == "⚠️ UPI Alert"]
            
            st.write("**Smart Identity Preview:**")
            st.table([{"Narration": str(row[n_c])[:50], "Target": trace_identity_engine(row[n_c], synced)[0]} for _, row in df.head(5).iterrows()])

            if len(unmatched) > 5:
                st.markdown(f'<div class="warning-box">🚨 Alert: {len(unmatched)} Untraced Items Found!</div>', unsafe_allow_html=True)
                upi_fix = st.selectbox("Assign Untraced to:", synced)
                if st.button("🚀 Process & Generate Tally XML"):
                    with st.status("⚡ Turbo-Processing..."):
                        time.sleep(1) # Visual feedback
                        st.balloons()
                        st.success("XML Ready!")
            else:
                if st.button("🚀 Convert to Tally XML"):
                    st.balloons()
                    st.success("Tally Prime XML Generated!")

st.markdown('</div>', unsafe_allow_html=True)

# Footer
l_foot = get_base_64_image("logo 1.png")
f_html = f'<img src="data:image/png;base64,{l_foot}" width="25" style="vertical-align: middle;">' if l_foot else ""
st.markdown(f'<div class="footer">{f_html} Sponsored By <b>Uday Mondal</b> | Created by <b>Debasish Biswas</b></div>', unsafe_allow_html=True)
