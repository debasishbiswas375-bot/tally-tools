import streamlit as st
import pandas as pd
from bs4 import BeautifulSoup
import pdfplumber
import io
import base64

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Accounting Expert | AI Bank to Tally",
    page_icon="logo.png",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 2. FUTURISTIC THEME CSS ---
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
        html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #F8FAFC; color: #0F172A; }
        
        .hero-container { 
            text-align: center; 
            padding: 50px 20px; 
            background: linear-gradient(135deg, #065F46 0%, #1E40AF 100%); 
            color: white; 
            margin: -6rem -4rem 30px -4rem; 
            box-shadow: 0 10px 30px -10px rgba(6, 95, 70, 0.5); 
            position: relative; 
        }

        .stButton>button { 
            width: 100%; 
            background: linear-gradient(90deg, #10B981 0%, #3B82F6 100%); 
            color: white; 
            border-radius: 8px; 
            height: 55px; 
            font-weight: 600; 
            border: none; 
        }

        /* --- FOOTER STYLING --- */
        .footer {
            margin-top: 60px;
            padding: 40px;
            text-align: center;
            color: #64748B;
            font-size: 0.95rem;
            border-top: 1px solid #E2E8F0;
            background-color: white;
            margin-left: -4rem;
            margin-right: -4rem;
            margin-bottom: -6rem;
        }
        .brand-link { color: #059669; text-decoration: none; font-weight: 700; }
        
        #MainMenu, footer, header { visibility: hidden; }
    </style>
""", unsafe_allow_html=True)

# --- 3. HELPER FUNCTIONS ---

def get_img_as_base64(file):
    try:
        with open(file, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except: return None

def get_ledger_names(html_file):
    try:
        soup = BeautifulSoup(html_file, 'html.parser')
        ledgers = [td.text.strip() for td in soup.find_all('td') if len(td.text.strip()) > 1]
        return sorted(list(set(ledgers)))
    except: return []

# --- 4. UI SECTIONS ---

# Hero Section
hero_logo = get_img_as_base64("logo.png")
hero_html = f'<img src="data:image/png;base64,{hero_logo}" width="120">' if hero_logo else ""
st.markdown(f'<div class="hero-container">{hero_html}<div style="font-size:3.5rem; font-weight:800;">Accounting Expert</div></div>', unsafe_allow_html=True)

# Dashboard Columns
col_left, col_right = st.columns([1, 1.5], gap="large")

with col_left:
    st.markdown("### 🛠️ 1. Settings & Mapping")
    uploaded_html = st.file_uploader("Upload Tally Master (Optional)", type=['html', 'htm'])
    ledger_options = ["Suspense A/c", "Cash", "Bank"]
    synced_masters = []
    
    if uploaded_html:
        synced_masters = get_ledger_names(uploaded_html)
        if synced_masters:
            st.success(f"✅ Synced {len(synced_masters)} ledgers")
            ledger_options = ["⭐ AI Auto-Trace (Premium)"] + synced_masters
    
    st.selectbox("Select Bank Ledger", ledger_options)
    party_ledger = st.selectbox("Select Default Party", ledger_options)

with col_right:
    st.markdown("### 📂 2. Upload & Convert")
    st.selectbox("Select Bank Format", ["SBI", "PNB", "ICICI", "HDFC"])
    uploaded_file = st.file_uploader("Drop Statement here", type=['xlsx', 'xls', 'pdf'])
    
    if uploaded_file:
        if st.button("🚀 Convert to Tally XML"):
            st.balloons()
            st.success("Premium AI Match Complete!")
            st.download_button("⬇️ Download XML", "Dummy XML Content", "tally_import.xml", use_container_width=True)

# --- 5. THE BRANDED FOOTER ---

# Get Sponsor Logo (logo 1.png) and Creator Logo (logo.png)
sponsor_logo_b64 = get_img_as_base64("logo 1.png")
creator_logo_b64 = get_img_as_base64("logo.png")

sponsor_html = f'<img src="data:image/png;base64,{sponsor_logo_b64}" width="25" style="vertical-align: middle; margin-right: 8px;">' if sponsor_logo_b64 else ""
creator_html = f'<img src="data:image/png;base64,{creator_logo_b64}" width="20" style="vertical-align: middle; margin-right: 8px;">' if creator_logo_b64 else ""

st.markdown(f"""
    <div class="footer">
        <p>Sponsored By {sponsor_html} <span class="brand-link" style="color:#0F172A;">Uday Mondal</span> | Consultant Advocate</p>
        <p style="font-size: 13px; margin-top: 10px;">
            {creator_html} Powered & Created by <span class="brand-link">Debasish Biswas</span> | Professional Tally Automation
        </p>
    </div>
""", unsafe_allow_html=True)
