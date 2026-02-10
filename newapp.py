import streamlit as st
import pandas as pd
from bs4 import BeautifulSoup
import pdfplumber
import base64

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Accounting Expert",
    page_icon="logo.png",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 2. SESSION STATE ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

# --- 3. CUSTOM CSS (FIXING READABILITY) ---
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
        
        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif;
            background-color: #0056D2; /* Keeping your blue theme */
        }

        /* Navbar Styling */
        .stTabs {
            background-color: #0056D2;
            padding-top: 10px;
            margin-top: -6rem; 
            position: sticky;
            top: 0;
            z-index: 999;
        }

        /* FORCING WHITE TEXT FOR VISIBILITY */
        .hero-title, .hero-subtitle, h1, h2, h3, p, label, .stMarkdown {
            color: #FFFFFF !important;
        }

        /* Input Box Labels (Specifically for dark backgrounds) */
        .stTextInput label, .stSelectbox label, .stFileUploader label {
            color: #FFFFFF !important;
            font-weight: 600 !important;
        }

        /* Pinned Footer at the Bottom */
        .footer {
            position: fixed;
            left: 0;
            bottom: 0;
            width: 100%;
            background-color: #FFFFFF; /* White footer for contrast */
            text-align: center;
            padding: 10px;
            border-top: 1px solid #E2E8F0;
            z-index: 1000;
        }
        
        .footer p, .footer span {
            color: #475569 !important; /* Dark text in the white footer */
        }

        /* Buttons */
        div[data-testid="stButton"] button {
            background-color: #66E035;
            color: #0056D2;
            border-radius: 50px;
            font-weight: 700;
            border: none;
        }
    </style>
""", unsafe_allow_html=True)

# --- 4. LOGIC FUNCTIONS ---
def get_img_as_base64(file):
    try:
        with open(file, "rb") as f: return base64.b64encode(f.read()).decode()
    except: return None

# --- 5. MAIN NAVIGATION ---
# Organized for a standard user flow
tabs = st.tabs(["Home", "Solutions", "Pricing", "Login", "Register"])

# TAB 1: HOME
with tabs[0]:
    st.markdown('<h1 class="hero-title">Perfecting the Science of Data Extraction</h1>', unsafe_allow_html=True)
    st.markdown('<p class="hero-subtitle">AI-powered tool to convert bank statements to Tally XML with 99% accuracy.</p>', unsafe_allow_html=True)
    
    if st.session_state.logged_in:
        st.markdown("### 🛠️ Welcome Back! Start Converting")
        # Your conversion tool UI (File uploader, etc.) would be placed here
    else:
        st.info("👋 Please Login or Register using the tabs above to start your conversion.")

# TAB 2: SOLUTIONS
with tabs[1]:
    st.markdown("## 🌟 Our Solutions")
    st.markdown("""
    * **Bank Statement to Tally**: Seamlessly import any bank PDF/Excel.
    * **Master Ledger Sync**: Auto-detect ledgers from your Tally HTML export.
    """)

# TAB 3: PRICING
with tabs[2]:
    st.markdown("## 💰 Simple Pricing")
    st.markdown("""
    * **Free Trial**: 10 conversions (No credit card).
    * **Pro Plan**: ₹499/month for unlimited conversions.
    """)

# TAB 4: LOGIN (Clean & Simple)
with tabs[3]:
    st.markdown("## 🔐 User Login")
    with st.form("login_form"):
        l_user = st.text_input("Username")
        l_pass = st.text_input("Password", type="password")
        if st.form_submit_button("Login"):
            # Simple check for your demo
            if l_user == "uday" and l_pass == "123":
                st.session_state.logged_in = True
                st.success("Logged in successfully!")
                st.rerun()
            else:
                st.error("Invalid credentials")

# TAB 5: REGISTER
with tabs[4]:
    st.markdown("## 🚀 Create Account")
    with st.form("reg_form"):
        st.text_input("Username")
        st.text_input("Email")
        st.text_input("Password", type="password")
        if st.form_submit_button("Register Now"):
            st.success("Account created! Please go to the Login tab.")

# --- 6. PINNED GLOBAL FOOTER ---
try: 
    uday_logo = get_img_as_base64("logo 1.png")
except: 
    uday_logo = None

uday_html = f'<img src="data:image/png;base64,{uday_logo}" width="20" style="vertical-align:middle; margin-right:5px;">' if uday_logo else ""

st.markdown(f"""
    <div class="footer">
        <p style="margin:0;">
            Sponsored By {uday_html} <b>Uday Mondal</b> | Consultant Advocate
        </p>
        <p style="margin:0; font-size: 12px;">
            Powered & Created by <b>Debasish Biswas</b>
        </p>
    </div>
""", unsafe_allow_html=True)
