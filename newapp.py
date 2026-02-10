import streamlit as st
import pandas as pd
from PIL import Image
from bs4 import BeautifulSoup
import pdfplumber
import io
import base64

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Accounting Expert",
    page_icon="logo.png",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 2. SESSION STATE ---
if 'users_db' not in st.session_state:
    st.session_state.users_db = pd.DataFrame([
        {"Username": "admin", "Password": "123", "Role": "Admin", "Status": "Active"},
        {"Username": "uday", "Password": "123", "Role": "User", "Status": "Active"}
    ])

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.current_user = None

# --- 3. CUSTOM CSS ---
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
        
        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif;
            background-color: #FFFFFF;
            color: #0F172A;
        }

        /* --- NAVIGATION TABS --- */
        .stTabs {
            background-color: #0056D2;
            padding-top: 10px;
            padding-bottom: 0px;
            margin-top: -6rem; 
            position: sticky;
            top: 0;
            z-index: 999;
            box-shadow: 0 4px 10px rgba(0,0,0,0.1);
        }

        .stTabs [data-baseweb="tab-list"] {
            gap: 20px;
            justify-content: flex-end;
            padding-right: 40px;
        }

        .stTabs [data-baseweb="tab"] {
            height: 60px;
            white-space: pre-wrap;
            background-color: transparent;
            border: none;
            color: rgba(255, 255, 255, 0.85);
            font-weight: 500;
            font-size: 1rem;
            padding: 0 15px;
        }

        .stTabs [aria-selected="true"] {
            background-color: #FFFFFF !important;
            color: #0056D2 !important;
            border-radius: 50px;
            font-weight: 700;
        }

        /* --- HERO SECTION (No Background) --- */
        .hero-container {
            background-color: transparent; 
            color: #0F172A;
            padding: 40px 60px 80px 60px;
            margin: 0 -4rem 0 -4rem;
        }
        
        .hero-title {
            font-size: 3.5rem;
            font-weight: 800;
            line-height: 1.1;
            margin-bottom: 20px;
            color: #0F172A !important;
        }
        
        .hero-subtitle {
            font-size: 1.2rem;
            opacity: 0.9;
            margin-bottom: 30px;
            line-height: 1.6;
            color: #475569 !important;
        }

        /* --- FORM CARDS --- */
        .auth-card {
            background-color: white;
            padding: 30px;
            border-radius: 12px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.15);
            color: #333;
            border: 1px solid #E2E8F0;
        }

        /* --- BUTTONS --- */
        div[data-testid="stButton"] button {
            background-color: #66E035;
            color: #0056D2;
            font-weight: 700;
            border-radius: 50px;
            border: none;
            width: 100%;
            padding: 12px;
        }

        /* Footer */
        .footer {
            margin-top: 100px;
            padding: 30px;
            text-align: center;
            color: #64748B;
            border-top: 1px solid #eee;
            background-color: white;
            margin-bottom: -50px;
        }
        
        #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- 4. LOGIC FUNCTIONS ---
def get_img_as_base64(file):
    try:
        with open(file, "rb") as f: data = f.read()
        return base64.b64encode(data).decode()
    except: return None

# ... (Previous Logic Functions for Ledger/PDF/XML processing remain unchanged)

# --- 5. MAIN NAVIGATION ---
tabs = st.tabs(["Home", "Solutions", "Pricing", "Login", "Start Free Trial"])

# --- TAB 1: HOME ---
with tabs[0]:
    with st.container():
        st.markdown('<div class="hero-container">', unsafe_allow_html=True)
        if st.session_state.logged_in:
            st.markdown(f"## Welcome back, {st.session_state.current_user}!")
        else:
            col_hero_left, col_hero_right = st.columns([1.5, 1], gap="large")
            with col_hero_left:
                st.markdown('<div class="hero-title">Perfecting the Science of Data Extraction</div>', unsafe_allow_html=True)
                st.markdown('<div class="hero-subtitle">AI-powered tool to convert bank statements and financial documents into Tally XML with 99% accuracy.</div>', unsafe_allow_html=True)
                
                # Your Own Logo
                try: 
                    my_logo_b64 = get_img_as_base64("logo.png")
                    if my_logo_b64: st.markdown(f'<img src="data:image/png;base64,{my_logo_b64}" width="150" style="margin-top:20px;">', unsafe_allow_html=True)
                except: pass

            with col_hero_right:
                st.markdown('<div class="auth-card">', unsafe_allow_html=True)
                st.markdown("### 🚀 Get Started")
                # ... (Registration form code)
                st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # --- MAIN TOOL AREA (If logged in) ---
    # ... (Converter Tool logic code)

# --- FOOTER ---
try: 
    uday_logo_b64 = get_img_as_base64("logo 1.png") # Uday Mondal's Logo
except: 
    uday_logo_b64 = None

uday_logo_html = f'<img src="data:image/png;base64,{uday_logo_b64}" width="25" style="vertical-align: middle;">' if uday_logo_b64 else ""

st.markdown(f"""
    <div class="footer">
        <p>Sponsored By {uday_logo_html} <span style="color:#0044CC; font-weight:700">Uday Mondal</span> | Consultant Advocate</p>
        <p style="font-size: 13px;">Powered & Created by <span style="color:#0044CC; font-weight:700">Debasish Biswas</span></p>
    </div>
""", unsafe_allow_html=True)
