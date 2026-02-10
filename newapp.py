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

# --- 2. SESSION STATE (DATABASE) ---
if 'users_db' not in st.session_state:
    st.session_state.users_db = pd.DataFrame([
        {"Username": "admin", "Password": "123", "Role": "Admin"},
        {"Username": "uday", "Password": "123", "Role": "User"}
    ])

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.current_user = None
    st.session_state.user_role = None

# --- 3. FINAL POLISHED CSS ---
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
        
        .stApp {
            background-color: #0056D2;
        }

        /* STICKY NAV BAR */
        .stTabs {
            background-color: #0056D2;
            padding-top: 10px;
            position: sticky;
            top: 0;
            z-index: 1000;
            border-bottom: 1px solid rgba(255,255,255,0.2);
        }

        /* TAB STYLING */
        .stTabs [data-baseweb="tab"] {
            color: #FFFFFF !important;
            font-weight: 600;
            padding: 10px 20px;
        }
        
        .stTabs [aria-selected="true"] {
            background-color: #FFFFFF !important;
            color: #0056D2 !important;
            border-radius: 8px 8px 0 0;
        }

        /* TEXT VISIBILITY */
        h1, h2, h3, p, span, label, .stMarkdown {
            color: #FFFFFF !important;
        }

        /* INPUT CONTRAST */
        .stTextInput label, .stSelectbox label, .stFileUploader label {
            color: #FFFFFF !important;
            font-size: 1rem !important;
        }

        /* PINNED WHITE FOOTER */
        .footer {
            position: fixed;
            left: 0;
            bottom: 0;
            width: 100%;
            background-color: #FFFFFF;
            text-align: center;
            padding: 12px;
            z-index: 2000;
            border-top: 1px solid #E2E8F0;
        }
        
        .footer p, .footer b {
            color: #1E293B !important;
            margin: 0;
        }

        /* ACCENT BUTTONS */
        div[data-testid="stButton"] button {
            background-color: #66E035;
            color: #0056D2;
            border-radius: 50px;
            font-weight: 700;
            border: none;
            padding: 10px 40px;
            transition: 0.3s;
        }
        div[data-testid="stButton"] button:hover {
            background-color: #5AC72E;
            transform: scale(1.05);
        }

        header {visibility: hidden;}
        #MainMenu {visibility: hidden;}
        .main .block-container { padding-bottom: 110px; }
    </style>
""", unsafe_allow_html=True)

# --- 4. LOGIC FUNCTIONS ---
def get_img_as_base64(file):
    try:
        with open(file, "rb") as f: return base64.b64encode(f.read()).decode()
    except: return None

# --- 5. NAVIGATION ---
tabs = st.tabs(["Home", "Solutions", "Pricing", "Login", "Register"])

# TAB 1: HOME
with tabs[0]:
    st.markdown('<h1>Perfecting the Science of Data Extraction</h1>', unsafe_allow_html=True)
    st.markdown('<p style="font-size:1.2rem; opacity:0.9;">AI-powered tool to convert bank statements to Tally XML with 99% accuracy.</p>', unsafe_allow_html=True)
    
    if st.session_state.logged_in:
        st.success(f"🔓 Logged in as: {st.session_state.current_user} ({st.session_state.user_role})")
        if st.button("Logout"):
            st.session_state.logged_in = False
            st.rerun()
        
        st.markdown("---")
        # INSERT CONVERTER TOOL HERE
        st.info("Converter Tool UI goes here.")
    else:
        st.warning("👋 Welcome! Please **Login** or **Register** to begin processing your files.")

# TAB 2: SOLUTIONS
with tabs[1]:
    st.markdown("## 🌟 Our Solutions")
    st.markdown("- **Bank Statement to Tally**: Smart PDF/Excel parsing.")
    st.markdown("- **Master Ledger Sync**: Auto-detect ledgers from Tally exports.")

# TAB 3: PRICING
with tabs[2]:
    st.markdown("## 💰 Simple Pricing")
    st.markdown("- **Trial**: First 10 conversions free.")
    st.markdown("- **Pro Plan**: ₹499/month for unlimited use.")

# TAB 4: LOGIN
with tabs[3]:
    st.markdown("## 🔐 User Access")
    l_user = st.text_input("Username", key="login_u")
    l_pass = st.text_input("Password", type="password", key="login_p")
    if st.button("Sign In"):
        db = st.session_state.users_db
        user_row = db[(db['Username'] == l_user) & (db['Password'] == l_pass)]
        if not user_row.empty:
            st.session_state.logged_in = True
            st.session_state.current_user = l_user
            st.session_state.user_role = user_row.iloc[0]['Role']
            st.success("Access Granted!")
            st.rerun()
        else:
            st.error("Invalid credentials.")

# TAB 5: REGISTER
with tabs[4]:
    st.markdown("## 🚀 Create Account")
    r_user = st.text_input("Username", key="reg_u")
    r_pass = st.text_input("Password", type="password", key="reg_p")
    if st.button("Create Account"):
        new_user = pd.DataFrame([{"Username": r_user, "Password": r_pass, "Role": "User"}])
        st.session_state.users_db = pd.concat([st.session_state.users_db, new_user], ignore_index=True)
        st.success("Account created! You can now Login.")

# --- 6. PINNED GLOBAL FOOTER ---
try: uday_logo = get_img_as_base64("logo 1.png")
except: uday_logo = None
uday_html = f'<img src="data:image/png;base64,{uday_logo}" width="20" style="vertical-align:middle; margin-right:5px;">' if uday_logo else ""

st.markdown(f"""
    <div class="footer">
        <p>Sponsored By {uday_html} <b>Uday Mondal</b> | Consultant Advocate</p>
        <p style="font-size: 11px; margin-top: 4px; color: #64748B !important;">
            Powered & Created by <b>Debasish Biswas</b>
        </p>
    </div>
""", unsafe_allow_html=True)
