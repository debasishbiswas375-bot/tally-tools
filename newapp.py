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

# --- 3. CUSTOM CSS (BETTER VISIBILITY) ---
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
        
        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif;
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

        /* Fix visibility of text on blue background */
        .hero-title {
            color: #FFFFFF !important;
            font-size: 3.5rem;
            font-weight: 800;
            margin-bottom: 10px;
        }
        
        .hero-subtitle {
            color: #F8FAFC !important; /* Off-white for better readability */
            font-size: 1.25rem;
            margin-bottom: 30px;
        }

        /* Standardize Form Labels */
        .stTextInput label, .stSelectbox label {
            color: #FFFFFF !important;
            font-weight: 600 !important;
        }

        /* Pinned Footer */
        .footer {
            position: fixed;
            left: 0;
            bottom: 0;
            width: 100%;
            background-color: #FFFFFF;
            text-align: center;
            padding: 10px;
            border-top: 1px solid #E2E8F0;
            z-index: 100;
        }

        /* Regular Button Styling */
        div[data-testid="stButton"] button {
            border-radius: 8px;
            padding: 10px 24px;
        }
    </style>
""", unsafe_allow_html=True)

# --- 4. LOGIC FUNCTIONS ---
def get_img_as_base64(file):
    try:
        with open(file, "rb") as f: return base64.b64encode(f.read()).decode()
    except: return None

# --- 5. MAIN NAVIGATION ---
tabs = st.tabs(["Home", "Solutions", "Pricing", "Login", "Register"])

# TAB 1: HOME
with tabs[0]:
    st.markdown('<div class="hero-title">Perfecting the Science of Data Extraction</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-subtitle">Convert bank statements to Tally XML with 99% accuracy.</div>', unsafe_allow_html=True)
    
    if st.session_state.logged_in:
        st.success("✅ Logged in. Use the tools below.")
        # Conversion Tool Logic would go here
    else:
        st.info("👋 Welcome! Please Login or Register to start converting files.")

# TAB 2: SOLUTIONS
with tabs[1]:
    st.markdown("<h2 style='color:white;'>Our Solutions</h2>", unsafe_allow_html=True)
    st.markdown("""
    <ul style='color:white; font-size:1.1rem;'>
        <li><strong>Bank to Tally:</strong> Smart PDF/Excel parsing.</li>
        <li><strong>Master Sync:</strong> Ledger auto-matching.</li>
    </ul>
    """, unsafe_allow_html=True)

# TAB 3: PRICING
with tabs[2]:
    st.markdown("<h2 style='color:white;'>Simple Pricing</h2>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Free Trial", "10 Files")
    with col2:
        st.metric("Pro Plan", "Unlimited")

# TAB 4: LOGIN (Regular Basis)
with tabs[3]:
    st.markdown("<h2 style='color:white;'>User Login</h2>", unsafe_allow_html=True)
    with st.container():
        l_user = st.text_input("Username", key="l_u")
        l_pass = st.text_input("Password", type="password", key="l_p")
        if st.button("Login"):
            if l_user == "uday" and l_pass == "123":
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("Invalid credentials")

# TAB 5: REGISTER
with tabs[4]:
    st.markdown("<h2 style='color:white;'>Create Account</h2>", unsafe_allow_html=True)
    r_user = st.text_input("Choose Username", key="r_u")
    r_pass = st.text_input("Choose Password", type="password", key="r_p")
    if st.button("Register"):
        st.success("Registration successful! Please go to the Login tab.")

# --- 6. PINNED FOOTER ---
try: uday_logo = get_img_as_base64("logo 1.png")
except: uday_logo = None

uday_html = f'<img src="data:image/png;base64,{uday_logo}" width="20" style="vertical-align:middle;">' if uday_logo else ""

st.markdown(f"""
    <div class="footer">
        <p style="margin:0; font-size:0.9rem; color:#475569;">
            Sponsored By {uday_html} <b>Uday Mondal</b> | Consultant Advocate
        </p>
        <p style="margin:0; font-size:0.8rem; color:#64748B;">
            Powered & Created by <b>Debasish Biswas</b>
        </p>
    </div>
""", unsafe_allow_html=True)
