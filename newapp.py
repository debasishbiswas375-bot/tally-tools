import streamlit as st
import pandas as pd
from bs4 import BeautifulSoup
import os
import base64

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Accounting Expert",
    page_icon="logo.png",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 2. PERSISTENT DATABASE LOGIC ---
DB_FILE = "users.csv"

def load_data():
    if os.path.exists(DB_FILE):
        return pd.read_csv(DB_FILE)
    else:
        # Initial inbuilt database
        return pd.DataFrame([
            {
                "Username": "admin", "Password": "123", "Role": "Admin", 
                "Status": "Paid", "Pic": None, "Name": "Admin User", 
                "Mobile": "0000000000", "Email": "admin@example.com"
            }
        ])

def save_data(df):
    df.to_csv(DB_FILE, index=False)

if 'users_db' not in st.session_state:
    st.session_state.users_db = load_data()

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.current_user = None
    st.session_state.user_role = None
    st.session_state.user_status = None

# --- 3. CUSTOM CSS (NAVBAR, LOGO & FOOTER) ---
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
        .stApp { background-color: #0056D2; }

        /* LOGO.PNG PLACEMENT (Top Left Green Circle Area) */
        [data-testid="stHeader"]::before {
            content: "";
            background-image: url("app/static/logo.png"); /* Ensure logo.png is in your app folder */
            background-size: contain;
            background-repeat: no-repeat;
            position: absolute;
            left: 40px;
            top: 20px;
            width: 120px;
            height: 60px;
            z-index: 9999;
        }

        /* TEXT VISIBILITY TO WHITE */
        h1, h2, h3, h4, p, label, .stMarkdown, [data-testid="stMarkdownContainer"] p { 
            color: #FFFFFF !important; 
        }

        /* NAVBAR TABS */
        .stTabs [data-baseweb="tab-list"] {
            gap: 15px; justify-content: flex-end;
            background-color: rgba(255, 255, 255, 0.05);
            padding: 10px 20px; border-radius: 12px; margin-bottom: 30px;
        }
        .stTabs [data-baseweb="tab"] { color: #FFFFFF !important; font-weight: 600 !important; }
        .stTabs [aria-selected="true"] {
            background-color: #FFFFFF !important; color: #0056D2 !important; border-radius: 50px !important; padding: 8px 20px !important;
        }

        /* PILL BUTTON DESIGN */
        div.stButton > button {
            background-color: #66E035 !important; color: #0056D2 !important;
            border-radius: 50px !important; font-weight: 700 !important;
            padding: 0.6rem 2.5rem !important; border: none !important;
        }

        /* INPUT VISIBILITY */
        input, .stSelectbox div { color: #000000 !important; font-weight: 500 !important; }

        /* PROFESSIONAL FOOTER STYLING */
        header {visibility: hidden;}
        .footer-container {
            position: fixed; left: 0; bottom: 0; width: 100%;
            background-color: #FFFFFF; border-top: 1px solid #E2E8F0;
            padding: 15px 0; z-index: 2000; text-align: center;
            font-family: 'Inter', sans-serif;
        }
        .footer-line1 { 
            display: flex; align-items: center; justify-content: center; 
            font-size: 16px; color: #64748B !important; margin-bottom: 4px;
        }
        .footer-line2 { font-size: 14px; color: #94A3B8 !important; }
        .footer-logo { height: 24px; margin: 0 8px; vertical-align: middle; }
        .name-highlight { color: #0F172A !important; font-weight: 800; }
        .dev-highlight { color: #00A389 !important; font-weight: 700; } /* Matches green in screenshot */
    </style>
""", unsafe_allow_html=True)

# --- 4. NAVIGATION ---
tabs = st.tabs(["Home", "Solutions", "Pricing", "Account"])

with tabs[0]: # HOME
    if st.session_state.logged_in:
        st.markdown(f"<h1>Welcome back, {st.session_state.current_user}!</h1>", unsafe_allow_html=True)
        if st.session_state.user_role == "Admin" or st.session_state.user_status == "Paid":
            st.markdown("### 🛠️ Converter Tool (Full Access)")
            c1, c2 = st.columns(2)
            with c1:
                with st.container(border=True):
                    st.markdown("#### 🛠️ 1. Settings & Mapping")
                    st.file_uploader("Upload Tally Master (master.html)", type=['html'], key="up_master")
                    st.selectbox("Select Bank Ledger", ["Cash", "Bank"], key="sel_ledger")
                    st.selectbox("Select Default Party", ["Cash", "Suspense"], key="sel_party")
            with col2:
                with st.container(border=True):
                    st.markdown("#### 📂 2. Upload & Convert")
                    st.selectbox("Select Bank Format", ["SBI", "HDFC", "ICICI"], key="sel_format")
                    st.file_uploader("Drop Bank Statement here", type=['pdf', 'xlsx'], key="up_stmt")
                    st.button("🚀 Process & Generate XML")
        else:
            st.warning("⚠️ Trial Mode: Please contact Admin to upgrade.")
    else:
        st.markdown('<h1>Perfecting the Science of Data Extraction</h1>', unsafe_allow_html=True)
        st.info("👋 Welcome! Please visit the **Account** tab to Sign In.")

with tabs[1]: # SOLUTIONS
    st.markdown("## 🚀 Our Solutions")
    st.write("- Automated Bank to Tally XML Conversion")
    st.write("- HTML Master Ledger Mapping")

with tabs[2]: # PRICING
    st.markdown("## 💰 Pricing Plans")
    p1, p2 = st.columns(2)
    with p1: st.button("Trial Plan (Free)", key="p_free")
    with p2: st.button("Professional Plan (Paid)", key="p_paid")

with tabs[3]: # ACCOUNT
    if not st.session_state.logged_in:
        mode = st.radio("Choose Action", ["Login", "Register"], horizontal=True)
        if mode == "Login":
            u_in = st.text_input("Username", key="l_u")
            p_in = st.text_input("Password", type="password", key="l_p")
            if st.button("Sign In"):
                db = st.session_state.users_db
                match = db[(db['Username'] == str(u_in)) & (db['Password'] == str(p_in))]
                if not match.empty:
                    st.session_state.logged_in = True
                    st.session_state.current_user = u_in
                    st.session_state.user_role = match.iloc[0]['Role']
                    st.session_state.user_status = match.iloc[0]['Status']
                    st.rerun()
                else: st.error("Invalid credentials.")
        else:
            r_name = st.text_input("Full Name *", key="r_n")
            r_mob = st.text_input("Mobile *", key="r_m")
            r_email = st.text_input("Email *", key="r_e")
            r_user = st.text_input("Username *", key="r_u")
            r_pass = st.text_input("Password *", type="password", key="r_p")
            r_pkg = st.selectbox("Select Package", ["Free", "Paid"], key="r_s")
            r_comp = st.text_input("Company (Optional)", key="r_c")
            
            if st.button("Create Account"):
                if all([r_name, r_mob, r_email, r_user, r_pass]):
                    new_user = {
                        "Username": r_user, "Password": r_pass, "Role": "Trial", 
                        "Status": r_pkg, "Pic": None, "Name": r_name, 
                        "Mobile": r_mob, "Email": r_email, "Company": r_comp if r_comp.strip() else "N/A"
                    }
                    st.session_state.users_db = pd.concat([st.session_state.users_db, pd.DataFrame([new_user])], ignore_index=True)
                    save_data(st.session_state.users_db)
                    st.success("✅ Registration Successful! Please switch to Login.")
                else: st.error("Please fill in all required (*) fields.")
    else:
        st.button("Sign Out", on_click=lambda: st.session_state.update({"logged_in": False}))

# --- 5. PROFESSIONAL FOOTER ---
# Make sure logo1.png is in your app folder
st.markdown("""
    <div class="footer-container">
        <div class="footer-line1">
            Sponsored By <img src="app/static/logo1.png" class="footer-logo"> <span class="name-highlight">Uday Mondal</span> | Consultant Advocate
        </div>
        <div class="footer-line2">
            Powered & Created by <span class="dev-highlight">Debasish Biswas</span> | Professional Tally Automation
        </div>
    </div>
""", unsafe_allow_html=True)
