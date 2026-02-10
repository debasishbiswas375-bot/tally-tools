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

# --- 2. SESSION STATE ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

# --- 3. CUSTOM CSS (FIXING NAV BAR, TEXT VISIBILITY & PINNED FOOTER) ---
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
        
        /* Set global background to Blue */
        .stApp {
            background-color: #0056D2;
        }

        /* NAVIGATION BAR FIX - Removed negative margins to make it visible */
        .stTabs {
            background-color: #0056D2;
            padding-top: 10px;
            position: sticky;
            top: 0;
            z-index: 999;
            border-bottom: 1px solid rgba(255,255,255,0.2);
        }

        /* TAB TEXT VISIBILITY */
        .stTabs [data-baseweb="tab"] {
            color: #FFFFFF !important;
            font-weight: 600;
            font-size: 1rem;
        }
        
        .stTabs [aria-selected="true"] {
            background-color: #FFFFFF !important;
            color: #0056D2 !important;
            border-radius: 8px 8px 0 0;
        }

        /* FORCING WHITE TEXT FOR ALL LABELS AND HEADINGS ON BLUE */
        h1, h2, h3, p, span, label, .stMarkdown {
            color: #FFFFFF !important;
        }

        /* INPUT FIELD LABELS & BOXES */
        .stTextInput label, .stSelectbox label, .stFileUploader label {
            color: #FFFFFF !important;
            font-weight: 600 !important;
        }

        /* PINNED GLOBAL FOOTER */
        .footer {
            position: fixed;
            left: 0;
            bottom: 0;
            width: 100%;
            background-color: #FFFFFF; /* White background for visibility */
            text-align: center;
            padding: 12px;
            z-index: 1000;
            border-top: 1px solid #E2E8F0;
        }
        
        .footer p, .footer span, .footer b {
            color: #1E293B !important; /* Dark text on white footer */
            margin: 0;
        }

        /* BUTTON STYLING */
        div[data-testid="stButton"] button {
            background-color: #66E035;
            color: #0056D2;
            border-radius: 50px;
            font-weight: 700;
            border: none;
            width: auto;
            padding: 10px 30px;
        }

        /* Hide Streamlit Header/Footer elements */
        header {visibility: hidden;}
        #MainMenu {visibility: hidden;}
        .stDeployButton {display:none;}
        
        /* Extra padding at bottom to prevent footer overlap */
        .main .block-container {
            padding-bottom: 100px;
        }
    </style>
""", unsafe_allow_html=True)

# --- 4. LOGIC FUNCTIONS ---
def get_img_as_base64(file):
    try:
        with open(file, "rb") as f: return base64.b64encode(f.read()).decode()
    except: return None

# --- 5. MAIN NAVIGATION (TABS) ---
tabs = st.tabs(["Home", "Solutions", "Pricing", "Login", "Register"])

# TAB 1: HOME
with tabs[0]:
    st.markdown('<h1 style="font-size: 3rem;">Perfecting the Science of Data Extraction</h1>', unsafe_allow_html=True)
    st.markdown('<p style="font-size: 1.2rem;">AI-powered tool to convert bank statements to Tally XML with 99% accuracy.</p>', unsafe_allow_html=True)
    
    if st.session_state.logged_in:
        st.success("✅ System Ready. Please upload your files in the tool section.")
        # Conversion UI (Logic to be expanded here)
    else:
        st.info("👋 Welcome! Please use the **Login** or **Register** tabs to begin processing your files.")

# TAB 2: SOLUTIONS
with tabs[1]:
    st.markdown("## 🌟 Our Solutions")
    st.markdown("""
    * **Bank Statement to Tally**: Supports SBI, HDFC, ICICI, and more.
    * **Master Ledger Sync**: Upload your Tally HTML master to auto-map ledgers.
    * **PDF Password Support**: Process protected bank statements instantly.
    """)

# TAB 3: PRICING
with tabs[2]:
    st.markdown("## 💰 Simple Pricing")
    st.markdown("""
    * **Trial**: First 10 conversions free.
    * **Professional**: Unlimited conversions for ₹499/month.
    """)

# TAB 4: LOGIN
with tabs[3]:
    st.markdown("## 🔐 User Login")
    with st.container():
        l_user = st.text_input("Username", key="l_user")
        l_pass = st.text_input("Password", type="password", key="l_pass")
        if st.button("Login Now"):
            if l_user == "uday" and l_pass == "123":
                st.session_state.logged_in = True
                st.success("Login Successful!")
                st.rerun()
            else:
                st.error("Invalid Username or Password.")

# TAB 5: REGISTER
with tabs[4]:
    st.markdown("## 🚀 Create Your Account")
    st.text_input("Full Name", key="r_name")
    st.text_input("Desired Username", key="r_user")
    st.text_input("Password", type="password", key="r_pass")
    if st.button("Register"):
        st.success("Registration successful! Please proceed to the Login tab.")

# --- 6. PINNED GLOBAL FOOTER ---
try: 
    uday_logo = get_img_as_base64("logo 1.png")
except: 
    uday_logo = None

uday_html = f'<img src="data:image/png;base64,{uday_logo}" width="20" style="vertical-align:middle; margin-right:5px;">' if uday_logo else ""

st.markdown(f"""
    <div class="footer">
        <p>
            Sponsored By {uday_html} <b>Uday Mondal</b> | Consultant Advocate
        </p>
        <p style="font-size: 11px; margin-top: 5px; color: #64748B !important;">
            Powered & Created by <b>Debasish Biswas</b>
        </p>
    </div>
""", unsafe_allow_html=True)
