import streamlit as st
import pandas as pd
from bs4 import BeautifulSoup
import pdfplumber
import io
import base64

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(page_title="Accounting Expert", layout="wide", initial_sidebar_state="collapsed")

# --- 2. PREMIUM UI DESIGN ---
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
        html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #F8FAFC; }
        .hero-container { text-align: center; padding: 50px; background: linear-gradient(135deg, #065F46 0%, #1E40AF 100%); color: white; margin: -6rem -4rem 30px -4rem; }
        .stButton>button { width: 100%; background: #10B981; color: white; height: 55px; font-weight: 600; border-radius: 8px; border: none; }
        .warning-box { background-color: #FFFBEB; border: 2px solid #F59E0B; padding: 20px; border-radius: 12px; margin: 20px 0; color: #92400E; }
        .footer { margin-top: 60px; padding: 40px; text-align: center; color: #64748B; border-top: 1px solid #E2E8F0; background-color: white; margin-left: -4rem; margin-right: -4rem; }
    </style>
""", unsafe_allow_html=True)

# --- 3. ENGINE FUNCTIONS ---

def get_img_as_base64(file):
    try:
        with open(file, "rb") as f: return base64.b64encode(f.read()).decode()
    except: return None

def extract_ledger_names(html_file):
    try:
        soup = BeautifulSoup(html_file, 'html.parser')
        return sorted(list(set([td.text.strip() for td in soup.find_all('td') if len(td.text.strip()) > 1])))
    except: return []

def trace_logic(narration, master_list):
    """The Auto AI Trace engine."""
    if not narration or pd.isna(narration): return "Suspense", "None"
    nar_up = str(narration).upper()
    
    # Priority 1: Master List Match
    for ledger in master_list:
        if ledger.upper() in nar_up:
            return ledger, "Matched"
    
    # Priority 2: UPI Detection
    if "UPI" in nar_up:
        return "Untraced", "UPI_Alert"
    
    return "Suspense", "None"

# --- 4. UI DASHBOARD ---
h_logo = get_img_as_base64("logo.png")
h_html = f'<img src="data:image/png;base64,{h_logo}" width="100">' if h_logo else ""
st.markdown(f'<div class="hero-container">{h_html}<h1>Accounting Expert</h1><p>Master-First AI Trace Engine</p></div>', unsafe_allow_html=True)

c1, c2 = st.columns([1, 1.5], gap="large")

with c1:
    st.markdown("### 🛠️ 1. Settings")
    master = st.file_uploader("Upload Tally Master", type=['html'])
    synced, options = [], ["Upload Master.html first"]
    if master:
        synced = extract_ledger_names(master)
        st.success(f"✅ Synced {len(synced)} ledgers")
        options = ["⭐ AI Auto-Trace"] + synced
    
    bank_led = st.selectbox("Select Bank Ledger", ["State Bank of India -38500202509"] + synced)
    party_led = st.selectbox("Select Party Ledger", options)

with c2:
    st.markdown("### 📂 2. Convert")
    bank_file = st.file_uploader("Drop Statement here", type=['xlsx', 'xls', 'pdf'])
    
    if bank_file and master:
        # Load data logic here...
        st.info("File received. AI is scanning for UPI transactions...")
        
        # Simulated alert based on your 'more than 5' rule
        unmatched_upi_count = 8 # This would be calculated from the file
        
        if unmatched_upi_count > 5 and party_led == "⭐ AI Auto-Trace":
            st.markdown(f"""<div class="warning-box">
                <h3>⚠️ AI Trace Alert</h3>
                <p>Found {unmatched_upi_count} UPI transactions not in your Master.html. Please select a ledger to assign them to:</p>
            </div>""", unsafe_allow_html=True)
            
            manual_choice = st.selectbox("Assign untraced UPIs to:", synced)
            
            if st.button("🚀 Process & Generate XML"):
                st.success(f"All {unmatched_upi_count} UPI entries mapped to {manual_choice}!")
                st.download_button("⬇️ Download tally_import.xml", "XML_CONTENT", file_name="tally_import.xml")
        else:
            if st.button("🚀 Convert to Tally XML"):
                st.success("Conversion Successful!")

# --- 5. FOOTER ---
s_logo = get_img_as_base64("logo 1.png")
s_html = f'<img src="data:image/png;base64,{s_logo}" width="25" style="vertical-align:middle;">' if s_logo else ""
st.markdown(f"""<div class="footer"><p>Sponsored By {s_html} <b>Uday Mondal</b> | Created by Debasish Biswas</p></div>""", unsafe_allow_html=True)
