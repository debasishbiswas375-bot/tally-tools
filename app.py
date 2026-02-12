import streamlit as st
import pandas as pd
from bs4 import BeautifulSoup
import pdfplumber
import re
import base64
import io

# --- 1. PAGE CONFIG ---
st.set_page_config(
    page_title="Accounting Expert | AI Bank to Tally", 
    page_icon="logo.png",
    layout="wide",
    initial_sidebar_state="expanded" 
)

# --- 2. SOLID UNIFIED THEME CSS ---
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700&display=swap');
        
        /* Set everything to the same solid background color */
        .stApp, [data-testid="stSidebar"], .main, .stSidebarContent, html, body {
            background-color: #0F172A !important;
            font-family: 'Inter', sans-serif;
            color: #F8FAFC !important;
        }

        /* Hero Section - Solid with a subtle border instead of gradient */
        .hero-container {
            text-align: center; 
            padding: 40px 20px;
            background-color: #1E293B; 
            color: white; 
            margin: -6rem -4rem 30px -4rem;
            border-bottom: 2px solid #10B981;
        }
        
        /* Solid Input Areas */
        .stContainer, div[data-testid="stVerticalBlock"] > div:has(div.stMarkdown) {
            background-color: #1E293B !important;
            padding: 25px; 
            border-radius: 12px; 
            border: 1px solid #334155;
            margin-bottom: 20px;
        }

        /* Sidebar Logo and Text */
        .sidebar-logo-text { font-size: 1.4rem; font-weight: 800; color: white; text-align: center; margin-bottom: 20px; }
        .sidebar-footer-text { font-size: 12px; color: #94A3B8; text-align: center; margin-top: 30px; }

        h1, h2, h3, p, span, label { color: white !important; }
        h3 { border-left: 5px solid #10B981; padding-left: 12px; font-weight: 700 !important; }

        /* Buttons */
        .stButton>button { 
            width: 100%; 
            background: #10B981; 
            color: white !important; 
            border-radius: 8px; 
            height: 50px; 
            font-weight: 700; 
            border: none;
        }
        .stButton>button:hover { background: #059669; }
        
        #MainMenu, footer, header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- 3. HELPER FUNCTIONS ---

def get_img_as_base64(file):
    try:
        with open(file, "rb") as f: return base64.b64encode(f.read()).decode()
    except: return None

def smart_normalize(df):
    """Deep Scanner to find headers and prevent empty XML exports."""
    if df is None or df.empty: return pd.DataFrame()
    df = df.dropna(how='all').reset_index(drop=True)
    
    header_idx = None
    for i, row in df.iterrows():
        row_str = " ".join([str(v).lower() for v in row.values if v is not None])
        if 'date' in row_str and ('narration' in row_str or 'particular' in row_str or 'desc' in row_str):
            header_idx = i
            break
            
    if header_idx is not None:
        df.columns = df.iloc[header_idx]
        df = df[header_idx + 1:].reset_index(drop=True)
    
    df.columns = df.columns.astype(str).str.strip().str.lower()
    new_df = pd.DataFrame()
    col_map = {
        'Date': ['date', 'txn', 'value'],
        'Narration': ['narration', 'particular', 'description'],
        'Debit': ['debit', 'withdrawal', 'out', 'dr'],
        'Credit': ['credit', 'deposit', 'in', 'cr']
    }
    for target, aliases in col_map.items():
        found = next((c for c in df.columns if any(a in c for a in aliases)), None)
        new_df[target] = df[found] if found else (0.0 if target in ['Debit', 'Credit'] else "UNTRACED")
    return new_df.dropna(subset=['Date'])

# --- 4. PERSISTENT SIDEBAR ---
with st.sidebar:
    side_logo_b64 = get_img_as_base64("logo.png")
    if side_logo_b64:
        st.markdown(f'<div style="text-align:center;"><img src="data:image/png;base64,{side_logo_b64}" width="120"></div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-logo-text">Accounting Expert</div>', unsafe_allow_html=True)
    
    with st.expander("👤 User Account", expanded=True):
        st.write("Status: **Online**")
        st.write("User: **Debasish**")
    
    with st.expander("💳 Solutions & Pricing"):
        st.write("Plan: **Pro Tier**")
    
    with st.expander("❓ Help & Support"):
        st.write("WhatsApp: +91 9002043666")

    # Sponsored Footer at bottom of Sidebar
    st.markdown('<div style="height: 100px;"></div>', unsafe_allow_html=True)
    footer_logo_b64 = get_img_as_base64("logo 1.png")
    footer_logo_html = f'<img src="data:image/png;base64,{footer_logo_b64}" width="20" style="vertical-align: middle;">' if footer_logo_b64 else ""
    
    st.markdown(f"""
        <div class="sidebar-footer-text">
            Sponsored By {footer_logo_html} <b>Uday Mondal</b><br>
            Consultant Advocate<br><br>
            Created & Powered by<br><b>Debasish Biswas</b><br>
            v2.1 Stable Build
        </div>
    """, unsafe_allow_html=True)

# --- 5. MAIN DASHBOARD ---
hero_logo_b64 = get_img_as_base64("logo.png")
hero_logo_html = f'<img src="data:image/png;base64,{hero_logo_b64}" width="100" style="margin-bottom:15px;">' if hero_logo_b64 else ""

st.markdown(f"""
    <div class="hero-container">
        {hero_logo_html}
        <div style="font-size: 2.8rem; font-weight: 800;">Accounting Expert</div>
        <div style="font-size: 1.1rem; opacity: 0.9;">Professional Smart AI Bank to Tally XML Automation</div>
    </div>
""", unsafe_allow_html=True)

col_left, col_right = st.columns([1, 1.5], gap="large")

with col_left:
    with st.container():
        st.markdown("### 🛠️ 1. Settings")
        master = st.file_uploader("Upload Tally Master (HTML)", type=['html'])
        ledger_list = ["Suspense A/c", "Cash", "Bank"]
        if master:
            soup = BeautifulSoup(master, 'html.parser')
            extracted = sorted(list(set([t.text.strip() for t in soup.find_all('td') if t.text.strip()])))
            if extracted: ledger_list = extracted; st.success(f"✅ {len(ledger_list)} Ledgers Synced")
        
        bank_led = st.selectbox("Bank Ledger", ledger_list)
        part_led = st.selectbox("Default Party", ledger_list)

with col_right:
    with st.container():
        st.markdown("### 📂 2. Statement Processing")
        stmt_file = st.file_uploader("Upload PDF or Excel", type=['pdf', 'xlsx'])
        
        if stmt_file:
            with st.status("🚀 Processing with AI Engine...", expanded=False) as status:
                if stmt_file.name.endswith('.pdf'):
                    with pdfplumber.open(stmt_file) as pdf:
                        data = []
                        for page in pdf.pages:
                            table = page.extract_table()
                            if table: data.extend(table)
                    df_raw = pd.DataFrame(data)
                else:
                    df_raw = pd.read_excel(stmt_file)

                df_clean = smart_normalize(df_raw)
                
                if not df_clean.empty and 'Date' in df_clean.columns:
                    status.update(label="✅ Ready!", state="complete")
                    st.write("**Preview:**")
                    st.dataframe(df_clean[['Date', 'Narration', 'Debit', 'Credit']].head(10), use_container_width=True)
                    
                    if st.button("🚀 GENERATE XML"):
                        st.balloons()
                else:
                    status.update(label="❌ Detection Failed", state="error")
                    st.error("I couldn't find the Date/Narration headers. Please check the PDF format.")
