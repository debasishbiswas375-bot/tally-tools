import streamlit as st
import pandas as pd
from bs4 import BeautifulSoup
import os

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
        # Default starting database
        return pd.DataFrame([
            {
                "Username": "admin", "Password": "123", "Role": "Admin", 
                "Status": "Paid", "Pic": None, "Name": "Admin User", 
                "Mobile": "0000000000", "Email": "admin@example.com", "Company": "Master Corp"
            }
        ])

def save_data(df):
    df.to_csv(DB_FILE, index=False)

# Initialize Session State from CSV
if 'users_db' not in st.session_state:
    st.session_state.users_db = load_data()

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.current_user = None
    st.session_state.user_role = None
    st.session_state.user_status = None

# --- 3. CUSTOM CSS (NAVBAR, BUTTONS & WHITE TEXT) ---
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
        .stApp { background-color: #0056D2; }

        /* NAVBAR TABS STYLE */
        .stTabs [data-baseweb="tab-list"] {
            gap: 15px; justify-content: flex-end;
            background-color: rgba(255, 255, 255, 0.05);
            padding: 10px 20px; border-radius: 12px; margin-bottom: 30px;
        }
        .stTabs [data-baseweb="tab"] { color: #FFFFFF !important; font-weight: 600 !important; font-size: 16px !important; }
        .stTabs [aria-selected="true"] {
            background-color: #FFFFFF !important; color: #0056D2 !important; border-radius: 50px !important; padding: 8px 20px !important;
        }

        /* PILL BUTTON DESIGN (GREEN BG + BLUE TEXT) */
        div.stButton > button {
            background-color: #66E035 !important; color: #0056D2 !important;
            border-radius: 50px !important; font-weight: 700 !important;
            padding: 0.6rem 2.5rem !important; border: none !important; font-size: 16px !important;
        }

        /* TEXT VISIBILITY */
        h1, h2, h3, h4, p, label, .stMarkdown { color: #FFFFFF !important; }
        input, .stSelectbox div { color: #000000 !important; font-weight: 500 !important; }

        /* CONTENT CARDS */
        .content-card {
            background-color: #FFFFFF; padding: 25px; border-radius: 15px;
            color: #1E293B !important; margin-bottom: 20px; border-top: 8px solid #66E035;
        }
        .content-card * { color: #1E293B !important; }

        header {visibility: hidden;}
        .footer {
            position: fixed; left: 0; bottom: 0; width: 100%;
            background-color: #FFFFFF; text-align: center; padding: 10px; z-index: 2000;
        }
        .footer * { color: #1E293B !important; margin: 0; }
        .footer img { height: 20px; vertical-align: middle; margin: 0 5px; }
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
                    st.markdown("#### 1. Settings")
                    st.selectbox("Bank Ledger", ["Cash", "Bank"])
            with c2:
                with st.container(border=True):
                    st.markdown("#### 2. Process")
                    st.selectbox("Bank Format", ["SBI", "HDFC", "ICICI"])
                    st.file_uploader("Upload Statement")
                    st.button("🚀 Process & Generate XML")
        else:
            st.warning("⚠️ Trial Mode: Please upgrade to a Paid account.")
    else:
        st.markdown("<h1>Data Extraction Excellence</h1>", unsafe_allow_html=True)
        st.info("👋 Please Sign In on the Account tab.")

with tabs[1]: # SOLUTIONS
    st.markdown("## 🚀 Solutions")
    st.markdown('<div class="content-card"><h4>Bank Statement to Tally</h4><p>Automated XML generation for all major Indian banks.</p></div>', unsafe_allow_html=True)

with tabs[2]: # PRICING
    st.markdown("## 💰 Pricing")
    p1, p2 = st.columns(2)
    with p1: st.markdown('<div class="content-card"><h4>Free</h4><b>₹0</b></div>', unsafe_allow_html=True)
    with p2: st.markdown('<div class="content-card"><h4>Paid</h4><b>Contact Admin</b></div>', unsafe_allow_html=True)

with tabs[3]: # ACCOUNT
    if not st.session_state.logged_in:
        mode = st.radio("Action", ["Login", "Register"], horizontal=True)
        if mode == "Login":
            u = st.text_input("Username", key="l_u")
            p = st.text_input("Password", type="password", key="l_p")
            if st.button("Sign In"):
                db = st.session_state.users_db
                user = db[(db['Username'] == str(u)) & (db['Password'] == str(p))]
                if not user.empty:
                    st.session_state.logged_in = True
                    st.session_state.current_user = u
                    st.session_state.user_role = user.iloc[0]['Role']
                    st.session_state.user_status = user.iloc[0]['Status']
                    st.rerun()
                else: st.error("Invalid credentials.")
        else:
            r_name = st.text_input("Name *", key="r_n")
            r_mob = st.text_input("Mobile *", key="r_m")
            r_email = st.text_input("Email *", key="r_e")
            r_user = st.text_input("Username *", key="r_u")
            r_pass = st.text_input("Password *", type="password", key="r_p")
            r_pkg = st.selectbox("Package", ["Free", "Paid"], key="r_s")
            r_comp = st.text_input("Company (Optional)", key="r_c")
            
            if st.button("Create Account"):
                if all([r_name, r_mob, r_email, r_user, r_pass]):
                    new_user = {
                        "Username": r_user, "Password": r_pass, "Role": "Trial", 
                        "Status": r_pkg, "Pic": None, "Name": r_name, 
                        "Mobile": r_mob, "Email": r_email, "Company": r_comp if r_comp else "N/A"
                    }
                    st.session_state.users_db = pd.concat([st.session_state.users_db, pd.DataFrame([new_user])], ignore_index=True)
                    save_data(st.session_state.users_db) # Save to CSV
                    st.success("✅ Account created! Switch to Login.")
                else: st.error("Please fill required fields.")
    else:
        if st.button("Logout"):
            st.session_state.logged_in = False
            st.rerun()

# --- 5. FOOTER ---
st.markdown('<div class="footer"><p>Sponsored By <img src="logo 1.png"> <b>Uday Mondal</b> | Powered by <b>Debasish Biswas</b></p></div>', unsafe_allow_html=True)
