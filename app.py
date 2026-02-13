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
    initial_sidebar_state="collapsed" # Starts closed like a mobile app
)

# --- 2. THE "IRONCLAD" UI ENGINE ---
st.markdown("""
    <style>
        /* Hide default Streamlit elements */
        header, .stDeployButton { visibility: hidden !important; display: none !important; }
        
        /* 🟢 THE 3-LINE HAMBURGER MENU (To Expand) */
        [data-testid="stSidebarCollapsedControl"] {
            background-color: #10B981 !important;
            border-radius: 8px !important;
            width: 45px !important;
            height: 45px !important;
            top: 15px !important;
            left: 15px !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            z-index: 999999 !important;
            border: 1px solid rgba(255,255,255,0.2) !important;
        }

        /* Hide the default Streamlit >> arrow */
        [data-testid="stSidebarCollapsedControl"] svg { display: none !important; }

        /* Draw the 3 lines using CSS */
        [data-testid="stSidebarCollapsedControl"]::before {
            content: "";
            width: 20px;
            height: 2px;
            background: white;
            position: absolute;
            box-shadow: 0 7px 0 white, 0 -7px 0 white;
        }

        /* ❌ THE "X" CLOSE BUTTON (Inside Sidebar) */
        /* This targets the Streamlit collapse button when the sidebar is open */
        [data-testid="stSidebar"] button[kind="headerNoSpacing"] {
            background-color: #10B981 !important;
            color: white !important;
            border-radius: 50% !important;
            top: 10px !important;
            right: 10px !important;
        }

        /* 👤 TOP RIGHT PROFILE */
        .user-mgmt-container {
            position: fixed; 
            top: 15px; 
            right: 15px; 
            z-index: 999999; 
            display: flex; 
            align-items: center;
        }
        .profile-pic {
            width: 45px; 
            height: 45px; 
            border-radius: 50%;
            border: 2px solid #10B981; 
            background-color: white;
        }

        /* SIDEBAR STYLING */
        [data-testid="stSidebar"] {
            background-color: #0F172A !important;
            border-right: 2px solid #10B981;
        }
        [data-testid="stSidebar"] * { color: white !important; }

        /* HERO SECTION */
        .hero-container {
            text-align: center; 
            padding: 50px 20px;
            background: linear-gradient(135deg, #065F46 0%, #1E40AF 100%);
            color: white; 
            margin: -6rem -4rem 30px -4rem;
        }
    </style>
""", unsafe_allow_html=True)

# --- 3. TOP NAVIGATION (Profile Icon) ---
st.markdown(f"""
    <div class="user-mgmt-container">
        <span style="color:white; margin-right:10px; font-weight:600;">Debasish</span>
        <img src="https://www.w3schools.com/howto/img_avatar.png" class="profile-pic">
    </div>
    """, unsafe_allow_html=True)

# --- 4. SIDEBAR ---
with st.sidebar:
    st.markdown('<br>', unsafe_allow_html=True)
    # Your Logo Placeholder
    st.image("https://www.w3schools.com/howto/img_avatar.png", width=80) 
    st.markdown('<h2 style="color: #10B981; margin-bottom:0;">Accounting Expert</h2>', unsafe_allow_html=True)
    st.caption("tallytools.in")
    st.divider()

    # User Section
    with st.expander("👤 User Account", expanded=True):
        st.write("**Account:** Debasish")
        st.write("**Tier:** Professional")
        st.button("Update Profile")

    # Help Section
    with st.expander("❓ Help & Support", expanded=False):
        st.write("WhatsApp: +91 9002043666")
        st.write("Email: support@tallytools.in")

    st.divider()
    st.write("v1.0.2-Stable")

# --- 5. DATA LOGIC ---
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

# --- 6. MAIN DASHBOARD ---
st.markdown('<div class="hero-container"><h1 style="font-size: 2.8rem;">Accounting Expert</h1><p>Convert Excel to Tally XML Instantly</p></div>', unsafe_allow_html=True)

layout_col1, layout_col2 = st.columns([1, 1], gap="large")

with layout_col1:
    st.subheader("🛠️ 1. Settings")
    with st.container(border=True):
        master = st.file_uploader("Upload Tally Master (HTML)", type=['html'])
        bank_led = st.selectbox("Select Bank Ledger", ["Suspense A/c", "HDFC Bank", "SBI Bank"])

with layout_col2:
    st.subheader("📂 2. Conversion")
    with st.container(border=True):
        stmt_file = st.file_uploader("Upload Statement (PDF/Excel)", type=['pdf', 'xlsx'])
        if stmt_file:
            st.success(f"Ready to convert: {stmt_file.name}")
            if st.button("🚀 GENERATE TALLY XML"):
                st.balloons()
                st.download_button("⬇️ Download XML", "Converted Content", "tally_import.xml")

st.markdown("<br><hr><center>© 2026 TallyTools.in | Berhampore, WB</center>", unsafe_allow_html=True)
