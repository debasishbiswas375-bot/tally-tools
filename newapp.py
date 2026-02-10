import streamlit as st
import pandas as pd
from bs4 import BeautifulSoup
import pdfplumber
import base64
import io

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Accounting Expert",
    page_icon="logo.png",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 2. SESSION STATE (DATABASE & AUTH) ---
if 'users_db' not in st.session_state:
    st.session_state.users_db = pd.DataFrame([
        {"Username": "admin", "Password": "123", "Role": "Admin"},
        {"Username": "uday", "Password": "123", "Role": "User"}
    ])

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.current_user = None

# --- 3. CSS (HIGH VISIBILITY & PINNED NAV) ---
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
        .stApp { background-color: #0056D2; }
        
        /* Fixed Nav Bar visibility */
        .stTabs {
            background-color: #0056D2;
            padding-top: 10px;
            position: sticky;
            top: 0;
            z-index: 1000;
        }
        .stTabs [data-baseweb="tab"] { color: #FFFFFF !important; font-weight: 600; }
        .stTabs [aria-selected="true"] { background-color: #FFFFFF !important; color: #0056D2 !important; border-radius: 8px; }

        /* White text for everything else */
        h1, h2, h3, p, label, .stMarkdown { color: #FFFFFF !important; }
        
        /* Pinned Footer */
        .footer {
            position: fixed;
            left: 0;
            bottom: 0;
            width: 100%;
            background-color: #FFFFFF;
            text-align: center;
            padding: 10px;
            z-index: 2000;
            border-top: 1px solid #ddd;
        }
        .footer p, .footer b { color: #333 !important; margin: 0; }
        
        /* Button Style */
        div[data-testid="stButton"] button {
            background-color: #66E035;
            color: #0056D2;
            border-radius: 50px;
            font-weight: 700;
            border: none;
            padding: 10px 40px;
        }
        header {visibility: hidden;}
        .main .block-container { padding-bottom: 100px; }
    </style>
""", unsafe_allow_html=True)

# --- 4. LOGIC FUNCTIONS ---
def get_img_as_base64(file):
    try:
        with open(file, "rb") as f: return base64.b64encode(f.read()).decode()
    except: return None

def load_bank_file(file):
    if file.name.lower().endswith('.pdf'):
        all_rows = []
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages:
                table = page.extract_table()
                if table: all_rows.extend(table)
        return pd.DataFrame(all_rows)
    return pd.read_excel(file)

# --- 5. MAIN APP ---
tabs = st.tabs(["Home", "Solutions", "Pricing", "Login", "Register"])

# TAB 1: HOME (THE WORKSPACE)
with tabs[0]:
    if st.session_state.logged_in:
        st.markdown(f"<h1>Welcome, {st.session_state.current_user}!</h1>", unsafe_allow_html=True)
        st.markdown("### 🛠️ Converter Tool (Your Work File)")
        
        # --- CONVERTER TOOL ENABLED ---
        col1, col2 = st.columns([1, 1.5], gap="large")
        with col1:
            st.markdown("#### 1. Config")
            bank_fmt = st.selectbox("Select Bank", ["SBI", "HDFC", "ICICI", "Axis"])
            pdf_pass = st.text_input("PDF Password (if any)", type="password")
        
        with col2:
            st.markdown("#### 2. Process")
            up_file = st.file_uploader("Upload Statement", type=['pdf', 'xlsx'])
            if up_file:
                st.success("File Received. Click below to start conversion.")
                if st.button("🚀 Process & Generate XML"):
                    st.balloons()
                    st.info("Generating XML for Tally...")
        
        if st.button("Logout"):
            st.session_state.logged_in = False
            st.rerun()
    else:
        st.markdown('<h1>Perfecting the Science of Data Extraction</h1>', unsafe_allow_html=True)
        st.markdown('<p style="font-size:1.2rem;">AI-powered tool to convert statements to Tally XML with 99% accuracy.</p>', unsafe_allow_html=True)
        st.info("👋 Access Restricted. Please Sign In using the **Login** tab to use the tool.")

# SOLUTIONS & PRICING
with tabs[1]: st.markdown("## 🌟 Solutions Coming Soon")
with tabs[2]: st.markdown("## 💰 Pricing Details Coming Soon")

# TAB 4: LOGIN (ADMIN ACCESS: admin / 123)
with tabs[3]:
    st.markdown("## 🔐 User Access")
    l_user = st.text_input("Username", key="login_field_u")
    l_pass = st.text_input("Password", type="password", key="login_field_p")
    
    if st.button("Sign In"):
        db = st.session_state.users_db
        # Validation
        if ((db['Username'] == l_user) & (db['Password'] == l_pass)).any():
            st.session_state.logged_in = True
            st.session_state.current_user = l_user
            st.success("Success! Click 'Home' to start working.")
            st.rerun()
        else:
            st.error("Invalid Username or Password.")

# TAB 5: REGISTER
with tabs[4]:
    st.markdown("## 🚀 Register")
    r_user = st.text_input("New Username")
    r_pass = st.text_input("New Password", type="password")
    if st.button("Create Account"):
        st.success("Account created! Now Sign In on the Login tab.")

# --- 6. PINNED FOOTER ---
try: uday_logo = get_img_as_base64("logo 1.png")
except: uday_logo = None
uday_html = f'<img src="data:image/png;base64,{uday_logo}" width="20" style="vertical-align:middle; margin-right:5px;">' if uday_logo else ""

st.markdown(f"""
    <div class="footer">
        <p>Sponsored By {uday_html} <b>Uday Mondal</b> | Consultant Advocate</p>
        <p style="font-size: 11px; color: #666 !important;">Powered & Created by <b>Debasish Biswas</b></p>
    </div>
""", unsafe_allow_html=True)
