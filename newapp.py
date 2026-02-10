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

# --- 2. IMAGE ENCODING (Ensures logos show regardless of path issues) ---
def get_base64_image(image_path):
    if os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    return ""

# Pre-load Base64 strings for both logos
logo_main_base64 = get_base64_image("logo.png")
logo_uday_base64 = get_base64_image("logo 1.png")

# --- 3. PERSISTENT DATABASE LOGIC ---
DB_FILE = "users.csv"

def load_data():
    if os.path.exists(DB_FILE):
        return pd.read_csv(DB_FILE)
    return pd.DataFrame([
        {
            "Username": "admin", "Password": "123", "Role": "Admin", 
            "Status": "Paid", "Name": "Admin User", "Mobile": "000", "Email": "admin@test.com", "Company": "Master"
        }
    ])

if 'users_db' not in st.session_state:
    st.session_state.users_db = load_data()

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.current_user = None
    st.session_state.user_role = None
    st.session_state.user_status = None

# --- 4. CSS (LOGO PLACEMENT & WHITE TEXT) ---
st.markdown(f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
        .stApp {{ background-color: #0056D2; }}

        /* --- THE LOGO: UPPER LEFT ADJUSTED --- */
        .top-left-logo {{
            position: fixed;
            left: 30px;
            top: 10px; /* Adjusted slightly upper side */
            width: 125px;
            z-index: 10001;
        }}

        /* --- FORCE ALL TEXTS TO WHITE --- */
        h1, h2, h3, h4, p, label, span, .stMarkdown, [data-testid="stMarkdownContainer"] p {{
            color: #FFFFFF !important;
        }}

        /* --- NAVBAR STYLING --- */
        .stTabs [data-baseweb="tab-list"] {{
            gap: 15px; justify-content: flex-end;
            background-color: rgba(255, 255, 255, 0.05);
            padding: 10px 20px; border-radius: 12px; margin-bottom: 30px;
        }}
        .stTabs [data-baseweb="tab"] {{ color: #FFFFFF !important; font-weight: 600 !important; font-size: 16px !important; }}
        .stTabs [aria-selected="true"] {{
            background-color: #FFFFFF !important; color: #0056D2 !important; border-radius: 50px !important; padding: 8px 20px !important;
        }}

        /* --- INPUT FIELD VISIBILITY --- */
        input, .stSelectbox div, [data-testid="stFileUploader"] * {{ 
            color: #000000 !important; 
            font-weight: 500 !important; 
        }}

        /* --- PILL BUTTON DESIGN --- */
        div.stButton > button {{
            background-color: #66E035 !important; color: #0056D2 !important;
            border-radius: 50px !important; font-weight: 700 !important;
            padding: 0.6rem 2.5rem !important; border: none !important; font-size: 16px !important;
        }}

        header {{visibility: hidden;}}

        /* --- PROFESSIONAL FOOTER --- */
        .footer-container {{
            position: fixed; left: 0; bottom: 0; width: 100%;
            background-color: #FFFFFF; text-align: center; padding: 12px 0; z-index: 2000;
        }}
        .footer-line1 {{ display: flex; align-items: center; justify-content: center; font-size: 16px; color: #64748B !important; margin-bottom: 3px; }}
        .footer-line2 {{ font-size: 13px; color: #94A3B8 !important; }}
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

with tabs[0]: # HOME
    if st.session_state.logged_in:
        st.markdown(f"<h1>Welcome back, {st.session_state.current_user}!</h1>", unsafe_allow_html=True)
        if st.session_state.user_role == "Admin" or st.session_state.user_status == "Paid":
            st.markdown("### 🛠️ Converter Tool (Full Access)")
            col1, col2 = st.columns(2, gap="large")
            with col1:
                with st.container(border=True):
                    st.markdown("#### 🛠️ 1. Settings & Mapping")
                    st.file_uploader("Upload Tally Master (master.html)", type=['html'], key="h_master")
                    st.selectbox("Select Bank Ledger", ["Cash", "Bank"], key="h_ledger")
            with col2:
                with st.container(border=True):
                    st.markdown("#### 📂 2. Upload & Convert")
                    st.selectbox("Select Bank Format", ["SBI", "HDFC", "ICICI"], key="h_format")
                    st.file_uploader("Drop Bank Statement here", type=['pdf', 'xlsx'], key="h_stmt")
                    st.button("🚀 Process & Generate XML")
        else:
            st.warning("⚠️ Trial Mode: Please contact Admin to upgrade.")
    else:
        st.markdown('<h1>Perfecting the Science of Data Extraction</h1>', unsafe_allow_html=True)
        st.info("👋 Welcome! Please visit the **Account** tab to Sign In.")

with tabs[1]: # SOLUTIONS
    st.markdown("## 🚀 Our Solutions")
    st.markdown("#### Bank Statement to Tally XML")
    st.write("Convert any major bank PDF or Excel to Tally Prime XML formats.")

with tabs[2]: # PRICING
    st.markdown("## 💰 Pricing Plans")
    p1, p2 = st.columns(2)
    with p1: st.button("Trial (Free)", key="p_f")
    with p2: st.button("Pro (Paid)", key="p_p")

with tabs[3]: # ACCOUNT (INTEGRATED & FIXED)
    if not st.session_state.logged_in:
        mode = st.radio("Choose Action", ["Login", "Register"], horizontal=True)
        if mode == "Login":
            u_in = st.text_input("Username", key="l_u")
            p_in = st.text_input("Password", type="password", key="l_p")
            if st.button("Sign In"):
                db = st.session_state.users_db
                match = db[(db['Username'] == u_in) & (db['Password'] == p_in)]
                if not match.empty:
                    st.session_state.logged_in = True
                    st.session_state.current_user = u_in
                    st.session_state.user_role = match.iloc[0]['Role']
                    st.session_state.user_status = match.iloc[0]['Status']
                    st.rerun()
                else: st.error("Invalid credentials.")
        else:
            r_name = st.text_input("Full Name *", key="r_name")
            r_mob = st.text_input("Mobile Number *", key="r_mob")
            r_email = st.text_input("Email ID *", key="r_email")
            r_user = st.text_input("Username *", key="r_user")
            r_pass = st.text_input("Password *", type="password", key="r_pass")
            r_pkg = st.selectbox("Select Package", ["Free", "Paid"], key="r_pkg")
            r_comp = st.text_input("Company Name (Optional)", key="r_comp")
            
            if st.button("Create Account"):
                # RECTIFIED: Validates only required fields
                required = [r_name, r_mob, r_email, r_user, r_pass]
                if all(v.strip() != "" for v in required):
                    new_user = {
                        "Username": r_user, "Password": r_pass, "Role": "Trial", "Status": r_pkg,
                        "Name": r_name, "Mobile": r_mob, "Email": r_email,
                        "Company": r_comp if r_comp.strip() else "N/A"
                    }
                    st.session_state.users_db = pd.concat([st.session_state.users_db, pd.DataFrame([new_user])], ignore_index=True)
                    st.session_state.users_db.to_csv(DB_FILE, index=False)
                    st.success("✅ Registration Successful! Switch to Login.")
                else:
                    st.error("Please fill in all required (*) fields.")
    else:
        st.button("Sign Out", on_click=lambda: st.session_state.update({"logged_in": False}))

# --- 7. PROFESSIONAL FOOTER ---
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
