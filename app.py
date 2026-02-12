import streamlit as st
import pandas as pd
from bs4 import BeautifulSoup
import pdfplumber
import re
import base64

# --- 1. PAGE CONFIG ---
st.set_page_config(
    page_title="Accounting Expert", 
    page_icon="logo.png",
    layout="wide",
    initial_sidebar_state="collapsed" 
)

# --- 2. THE "IRONCLAD" UI ENGINE ---
st.markdown("""
    <style>
        /* Hide all Streamlit default headers and footers */
        header, footer, .stDeployButton { visibility: hidden !important; display: none !important; }
        
        /* 🟢 FLOATING SIDEBAR ICON (LEFT) */
        [data-testid="stSidebarCollapsedControl"] {
            background: #10B981 !important;
            color: white !important;
            width: 55px !important;
            height: 55px !important;
            border-radius: 50% !important;
            top: 15px !important;
            left: 15px !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            box-shadow: 0 4px 15px rgba(0,0,0,0.3) !important;
            z-index: 99999999 !important; /* Extremely high priority */
            position: fixed !important;
            border: 2px solid white !important;
        }
        [data-testid="stSidebarCollapsedControl"] svg { fill: white !important; width: 30px !important; height: 30px !important; }

        /* 👤 SILENT PROFILE ICON (TOP RIGHT) */
        .user-mgmt-container {
            position: fixed; 
            top: 15px; 
            right: 15px; 
            z-index: 99999999; 
            display: flex; 
            flex-direction: column; 
            align-items: flex-end;
        }
        .profile-pic {
            width: 55px; 
            height: 55px; 
            border-radius: 50%;
            border: 2px solid #10B981; 
            background-color: white;
            cursor: pointer; 
            box-shadow: 0 4px 12px rgba(0,0,0,0.2);
            object-fit: cover;
        }
        .user-dropdown {
            display: none; 
            width: 220px; 
            background: white;
            border-radius: 12px; 
            box-shadow: 0 12px 30px rgba(0,0,0,0.3);
            padding: 18px; 
            margin-top: 10px; 
            border: 1px solid #E2E8F0;
        }
        .user-mgmt-container:hover .user-dropdown { display: block; }
        
        .user-dropdown h4 { color: #0F172A; margin: 0; font-size: 16px; font-weight: 700; }
        .user-dropdown p { color: #10B981; font-size: 13px; margin: 2px 0 15px 0; font-weight: 600; }
        
        .menu-item {
            display: block; padding: 10px 0; color: #334155 !important;
            font-size: 14px; text-decoration: none; border-bottom: 1px solid #F1F5F9;
            cursor: pointer;
        }

        /* HERO & THEME */
        .hero-container {
            text-align: center; padding: 60px 20px;
            background: linear-gradient(135deg, #065F46 0%, #1E40AF 100%);
            color: white; margin: -6rem -4rem 30px -4rem;
        }
        [data-testid="stSidebar"] { background-color: #0F172A !important; }
        [data-testid="stSidebar"] * { color: white !important; }
    </style>
""", unsafe_allow_html=True)

# --- 3. INJECT CUSTOM UI ---
st.markdown(f"""
    <div class="user-mgmt-container">
        <img src="https://www.w3schools.com/howto/img_avatar.png" class="profile-pic">
        <div class="user-dropdown">
            <h4>Debasish</h4>
            <p>Professional Tier</p>
            <div class="menu-item">🔑 Change Password</div>
            <div class="menu-item">🖼️ Update Picture</div>
            <div class="menu-item">⚡ Upgrade Tier</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# --- 4. DATA LOGIC ---
def clean_currency(value):
    if pd.isna(value) or value == '': return 0.0
    val = re.sub(r'[^\d.]', '', str(value))
    try: return float(val)
    except: return 0.0

def smart_normalize(df):
    if df is None or df.empty: return pd.DataFrame()
    df = df.dropna(how='all', axis=0).reset_index(drop=True)
    header_idx = None
    for i, row in df.iterrows():
        clean_row = [str(v).lower().strip() for v in row.values if v is not None]
        if 'date' in " ".join(clean_row):
            header_idx = i
            break
    if header_idx is not None:
        df.columns = df.iloc[header_idx]
        df = df[header_idx + 1:].reset_index(drop=True)
    df.columns = df.columns.astype(str).str.strip().str.lower()
    new_df = pd.DataFrame()
    col_map = {'Date':['date','txn'],'Narration':['narration','particular'],'Debit':['debit','dr'],'Credit':['credit','cr']}
    for target, aliases in col_map.items():
        found = next((c for c in df.columns if any(a in c for a in aliases)), None)
        new_df[target] = df[found] if found else (0.0 if target in ['Debit', 'Credit'] else "")
    return new_df

# --- 5. SIDEBAR ---
with st.sidebar:
    st.markdown('<h2 style="color: #10B981; text-align:center;">Accounting Expert</h2>', unsafe_allow_html=True)
    st.write("User: **Debasish**")
    st.write("WhatsApp: +91 9002043666")

# --- 6. MAIN DASHBOARD ---
st.markdown('<div class="hero-container"><h1 style="font-size: 2.5rem; font-weight: 800;">Accounting Expert</h1></div>', unsafe_allow_html=True)

c1, c2 = st.columns([1, 1.5], gap="large")
with c1:
    with st.container():
        st.markdown("### 🛠️ 1. Settings")
        master = st.file_uploader("Upload Tally Master (HTML)", type=['html'])
        bank_led = st.selectbox("Bank Ledger", ["Suspense A/c"])

with c2:
    with st.container():
        st.markdown("### 📂 2. Conversion")
        stmt_file = st.file_uploader("Upload PDF or Excel", type=['pdf', 'xlsx'])
        if stmt_file:
            st.success("File Received! Click Generate below.")
            if st.button("🚀 GENERATE XML"):
                st.download_button("⬇️ Download XML", "Dummy XML Content", "tally_import.xml")
