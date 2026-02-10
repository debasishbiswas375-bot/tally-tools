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

# --- 2. IMAGE ENCODING (Base64) ---
# This ensures logos show up even if the folder path is tricky
def get_base64_image(image_path):
    if os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    return ""

logo_main_base64 = get_base64_image("logo.png")
logo_uday_base64 = get_base64_image("logo 1.png")

# --- 3. PERSISTENT DATABASE ---
DB_FILE = "users.csv"
def load_data():
    if os.path.exists(DB_FILE):
        return pd.read_csv(DB_FILE)
    return pd.DataFrame([{"Username": "admin", "Password": "123", "Role": "Admin", "Status": "Paid"}])

if 'users_db' not in st.session_state:
    st.session_state.users_db = load_data()

# --- 4. CSS (LOGO PLACEMENT & WHITE TEXT) ---
st.markdown(f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
        .stApp {{ background-color: #0056D2; }}

        /* --- THE LOGO FIX: UPPER LEFT CORNER --- */
        .top-left-logo {{
            position: fixed;
            left: 10px;
            top: 10px;
            width: 130px; /* Adjust size as needed */
            z-index: 10001;
        }}

        /* --- NAVBAR STYLING --- */
        .stTabs [data-baseweb="tab-list"] {{
            gap: 15px; justify-content: flex-end;
            background-color: rgba(255, 255, 255, 0.05);
            padding: 10px 20px; border-radius: 12px; margin-bottom: 30px;
        }}
        .stTabs [data-baseweb="tab"] {{ color: #FFFFFF !important; font-weight: 600 !important; }}
        .stTabs [aria-selected="true"] {{
            background-color: #FFFFFF !important; color: #0056D2 !important; border-radius: 50px !important; padding: 8px 20px !important;
        }}

        /* --- TEXT COLORS --- */
        h1, h2, h3, h4, p, label, .stMarkdown, [data-testid="stMarkdownContainer"] p {{
            color: #FFFFFF !important;
        }}
        input, .stSelectbox div {{ color: #000000 !important; font-weight: 500 !important; }}

        /* --- BUTTONS --- */
        div.stButton > button {{
            background-color: #66E035 !important; color: #0056D2 !important;
            border-radius: 50px !important; font-weight: 700 !important;
            padding: 0.6rem 2.5rem !important; border: none !important;
        }}

        header {{visibility: hidden;}}

        /* --- PROFESSIONAL FOOTER --- */
        .footer-container {{
            position: fixed; left: 0; bottom: 0; width: 100%;
            background-color: #FFFFFF; text-align: center; padding: 15px 0; z-index: 2000;
        }}
        .footer-line1 {{ display: flex; align-items: center; justify-content: center; font-size: 16px; color: #64748B !important; margin-bottom: 4px; }}
        .footer-line2 {{ font-size: 14px; color: #94A3B8 !important; }}
        .footer-logo {{ height: 22px; margin: 0 8px; vertical-align: middle; }}
        .name-highlight {{ color: #0F172A !important; font-weight: 800; }}
        .dev-highlight {{ color: #00A389 !important; font-weight: 700; }}
    </style>
""", unsafe_allow_html=True)

# --- 5. LOGO RENDERING ---
if logo_main_base64:
    st.markdown(f'<img src="data:image/png;base64,{logo_main_base64}" class="top-left-logo">', unsafe_allow_html=True)

# --- 6. NAVIGATION ---
tabs = st.tabs(["Home", "Solutions", "Pricing", "Account"])

# ... (Previous logic for Home, Solutions, and Pricing goes here)

with tabs[3]: # ACCOUNT (FIXED REGISTRATION)
    if not st.session_state.get('logged_in', False):
        mode = st.radio("Choose Action", ["Login", "Register"], horizontal=True)
        if mode == "Register":
            r_name = st.text_input("Full Name *", key="reg_n")
            r_mob = st.text_input("Mobile Number *", key="reg_m")
            r_email = st.text_input("Email ID *", key="reg_e")
            r_user = st.text_input("Username *", key="reg_u")
            r_pass = st.text_input("Password *", type="password", key="reg_p")
            r_pkg = st.selectbox("Select Package", ["Free", "Paid"], key="reg_s")
            r_comp = st.text_input("Company Name (Optional)", key="reg_c")
            
            if st.button("Create Account"):
                required = [r_name, r_mob, r_email, r_user, r_pass]
                if all(v.strip() != "" for v in required):
                    new_user = {
                        "Username": r_user, "Password": r_pass, "Role": "Trial", "Status": r_pkg,
                        "Name": r_name, "Mobile": r_mob, "Email": r_email,
                        "Company": r_comp if r_comp.strip() else "N/A"
                    }
                    st.session_state.users_db = pd.concat([st.session_state.users_db, pd.DataFrame([new_user])], ignore_index=True)
                    st.session_state.users_db.to_csv(DB_FILE, index=False)
                    st.success("✅ Registration Successful! Please switch to Login.")
                else:
                    st.error("Please fill in all required (*) fields.")

# --- 7. FOOTER RENDERING ---
footer_logo_html = f'<img src="data:image/png;base64,{logo_uday_base64}" class="footer-logo">' if logo_uday_base64 else ""
st.markdown(f"""
    <div class="footer-container">
        <div class="footer-line1">
            Sponsored By {footer_logo_html} <span class="name-highlight">Uday Mondal</span> | Consultant Advocate
        </div>
        <div class="footer-line2">
            Powered & Created by <span class="dev-highlight">Debasish Biswas</span> | Professional Tally Automation
        </div>
    </div>
""", unsafe_allow_html=True)
