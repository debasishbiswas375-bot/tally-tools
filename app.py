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
    initial_sidebar_state="expanded" 
)

# --- 2. THE "IRONCLAD" UI ENGINE ---
st.markdown("""
    <style>
        /* Hide Streamlit default headers */
        header, .stDeployButton { visibility: hidden !important; display: none !important; }
        
        /* 🟢 FLOATING SIDEBAR ICON (For Mobile) */
        [data-testid="stSidebarCollapsedControl"] {
            background: #10B981 !important;
            color: white !important;
            width: 50px !important;
            height: 50px !important;
            border-radius: 50% !important;
            top: 15px !important;
            left: 15px !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            box-shadow: 0 4px 15px rgba(0,0,0,0.3) !important;
            z-index: 999999 !important;
            position: fixed !important;
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
            cursor: pointer;
            object-fit: cover;
        }

        /* SIDEBAR STYLING */
        [data-testid="stSidebar"] {
            background-color: #0F172A !important;
            border-right: 1px solid #1E293B;
        }
        [data-testid="stSidebar"] * { color: white !important; }
        
        /* CUSTOM CLOSE "X" ICON */
        .sidebar-close-text {
            position: absolute;
            top: -10px;
            right: 10px;
            font-size: 28px;
            color: #10B981;
            font-weight: bold;
            pointer-events: none; /* Let the actual arrow handle the click */
        }

        /* HERO SECTION */
        .hero-container {
            text-align: center; 
            padding: 50px 20px;
            background: linear-gradient(135deg, #065F46 0%, #1E40AF 100%);
            color: white; 
            margin: -6rem -4rem 30px -4rem;
        }
        
        /* Buttons Styling */
        .stButton>button {
            background-color: #10B981 !important;
            color: white !important;
            border-radius: 8px !important;
            border: none !important;
            width: 100%;
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

# --- 4. SIDEBAR (With "X" and Minimize features) ---
with st.sidebar:
    # Visual "X" hint next to the real collapse button
    st.markdown('<div class="sidebar-close-text">×</div>', unsafe_allow_html=True)
    
    st.markdown('<h2 style="color: #10B981; margin-bottom:0;">Accounting Expert</h2>', unsafe_allow_html=True)
    st.caption("Professional Solutions")
    st.divider()

    # MINIMIZE OPTION: User Account Expander
    with st.expander("👤 User Account", expanded=True):
        st.write("**Account:** Debasish")
        st.write("**Tier:** Professional")
        st.button("Edit Profile")

    # MINIMIZE OPTION: Help & Support
    with st.expander("❓ Help & Support", expanded=False):
        st.write("WhatsApp: +91 9002043666")
        st.write("Email: support@tallytools.in")
        st.write("Location: Berhampore, WB")

    st.divider()
    st.info("Tip: Use the '>>' arrow at the top to fully hide this menu.")

# --- 5. DATA LOGIC (Cleaning & Conversion) ---
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
st.markdown('<div class="hero-container"><h1 style="font-size: 2.8rem;">Accounting Expert</h1><p>Excel to Tally XML Converter</p></div>', unsafe_allow_html=True)

layout_col1, layout_col2 = st.columns([1, 1], gap="large")

with layout_col1:
    st.subheader("🛠️ Step 1: Configuration")
    with st.container(border=True):
        master = st.file_uploader("Upload Tally Master (HTML)", type=['html'])
        bank_led = st.selectbox("Bank Ledger", ["Suspense A/c", "HDFC Bank", "SBI Bank"])
        st.write("---")
        st.checkbox("Auto-detect columns", value=True)

with layout_col2:
    st.subheader("📂 Step 2: Conversion")
    with st.container(border=True):
        stmt_file = st.file_uploader("Upload Bank Statement (PDF/Excel)", type=['pdf', 'xlsx'])
        if stmt_file:
            st.success(f"File '{stmt_file.name}' ready!")
            if st.button("🚀 GENERATE XML"):
                # Placeholder for your XML logic
                st.balloons()
                st.download_button("⬇️ Download XML", "Converted XML Content", "tally_import.xml")

st.markdown("<br><hr><center>Developed for debasish.biswas375 | TallyTools.in</center>", unsafe_allow_html=True)
