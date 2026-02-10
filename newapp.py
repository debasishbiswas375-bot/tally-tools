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
def get_base64_image(image_path):
    if os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    return ""

logo_main_b64 = get_base64_image("logo.png")
logo_uday_b64 = get_base64_image("logo 1.png")

# --- 3. PERSISTENT DATABASE ---
DB_FILE = "users.csv"
def load_data():
    if os.path.exists(DB_FILE):
        return pd.read_csv(DB_FILE)
    return pd.DataFrame([{"Username": "admin", "Password": "123", "Role": "Admin", "Status": "Paid", "Name": "Admin User"}])

if 'users_db' not in st.session_state:
    st.session_state.users_db = load_data()

# --- 4. CSS (RECTIFIED LOGO, WHITE TEXT & FOOTER) ---
st.markdown(f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
        .stApp {{ background-color: #0056D2; padding-bottom: 100px; }}

        /* LOGO: UPPER LEFT CORNER ADJUSTED */
        .top-left-logo {{
            position: fixed; left: 30px; top: 5px; width: 115px; z-index: 10001;
        }}

        /* FORCE ALL TEXTS TO WHITE */
        h1, h2, h3, h4, p, label, span, .stMarkdown, [data-testid="stMarkdownContainer"] p {{
            color: #FFFFFF !important;
        }}

        /* NAVBAR TABS */
        .stTabs [data-baseweb="tab-list"] {{
            gap: 15px; justify-content: flex-end;
            background-color: rgba(255, 255, 255, 0.05);
            padding: 10px 20px; border-radius: 12px; margin-bottom: 30px;
        }}
        .stTabs [data-baseweb="tab"] {{ color: #FFFFFF !important; font-weight: 600 !important; font-size: 16px !important; }}
        .stTabs [aria-selected="true"] {{
            background-color: #FFFFFF !important; color: #0056D2 !important; border-radius: 50px !important; padding: 8px 20px !important;
        }}

        /* INPUTS & PILL BUTTONS */
        input, .stSelectbox div, [data-testid="stFileUploader"] * {{ color: #000000 !important; font-weight: 500 !important; }}
        div.stButton > button {{
            background-color: #66E035 !important; color: #0056D2 !important;
            border-radius: 50px !important; font-weight: 700 !important;
            padding: 0.6rem 2.5rem !important; border: none !important;
        }}

        /* WHITE CONTENT CARDS */
        .content-card {{
            background-color: #FFFFFF; padding: 25px; border-radius: 15px;
            color: #1E293B !important; margin-bottom: 20px; border-top: 8px solid #66E035;
        }}
        .content-card * {{ color: #1E293B !important; }}

        header {{visibility: hidden;}}

        /* RECTIFIED FOOTER: ENSURING BOTH LINES SHOW */
        .footer-container {{
            position: fixed; left: 0; bottom: 0; width: 100%;
            background-color: #FFFFFF; text-align: center; 
            padding: 15px 0 20px 0; z-index: 2000;
            border-top: 1px solid #E2E8F0;
        }}
        .footer-line1 {{ display: flex; align-items: center; justify-content: center; font-size: 16px; color: #64748B !important; margin-bottom: 6px; }}
        .footer-line2 {{ display: block; font-size: 14px; color: #94A3B8 !important; }}
        .footer-logo {{ height: 24px; margin: 0 10px; vertical-align: middle; }}
        .name-highlight {{ color: #0F172A !important; font-weight: 800; }}
        .dev-highlight {{ color: #00A389 !important; font-weight: 700; }}
    </style>
""", unsafe_allow_html=True)

# --- 5. LOGO RENDERING ---
if logo_main_b64:
    st.markdown(f'<img src="data:image/png;base64,{logo_main_b64}" class="top-left-logo">', unsafe_allow_html=True)

# --- 6. NAVIGATION ---
tabs = st.tabs(["Home", "Solutions", "Pricing", "Account"])

with tabs[0]: # HOME
    if st.session_state.get('logged_in', False):
        st.markdown(f"<h1>Welcome back, {st.session_state.current_user}!</h1>", unsafe_allow_html=True)
        if st.session_state.user_role == "Admin" or st.session_state.user_status == "Paid":
            st.markdown("### 🛠️ Converter Tool (Full Access)")
            col1, col2 = st.columns(2, gap="large")
            with col1:
                with st.container(border=True):
                    st.markdown("#### 🛠️ 1. Settings & Mapping")
                    st.file_uploader("Upload Tally Master (master.html)", type=['html'], key="h_m")
                    st.selectbox("Select Bank Ledger (1st Ledger)", ["Cash", "HDFC Bank", "SBI Bank"], key="l1")
                    st.selectbox("Select Party Ledger (2nd Ledger)", ["Suspense Account", "Sales"], key="l2")
            with col2:
                with st.container(border=True):
                    st.markdown("#### 📂 2. Upload & Convert")
                    st.selectbox("Select Indian Bank Format", ["SBI", "HDFC", "ICICI", "Axis", "PNB", "BOB", "IDFC", "Canara"], key="h_f")
                    st.file_uploader("Drop Bank Statement (PDF/XLSX)", type=['pdf', 'xlsx'], key="h_s")
                    st.button("🚀 Process & Generate XML")
        else:
            st.warning("⚠️ Trial Mode: Please upgrade to a Paid account.")
    else:
        st.markdown('<h1>Perfecting the Science of Data Extraction</h1>', unsafe_allow_html=True)
        st.info("👋 Use the Account tab to Sign In.")

with tabs[1]: # SOLUTIONS
    st.markdown("## 🚀 Our Core Solutions")
    st.markdown("""
        <div class="content-card">
            <h4>🏦 All Indian Banks Statement Mapping</h4>
            <p>We provide specialized mapping for all major Indian banks including SBI, HDFC, ICICI, PNB, and Axis. Simply select your bank format, and our engine handles the complex parsing instantly.</p>
        </div>
        <div class="content-card">
            <h4>📊 Tally XML Automation</h4>
            <p>Automatically generate Tally Prime compatible XML files. No more manual data entry or accounting errors.</p>
        </div>
    """, unsafe_allow_html=True)

with tabs[2]: # PRICING
    st.markdown("## 💰 Professional Pricing")
    st.markdown('<div class="content-card"><h4>Professional Plan</h4><p>Unlock all Indian bank formats and unlimited XML exports.</p><b>Contact Admin for Paid Access</b></div>', unsafe_allow_html=True)

with tabs[3]: # ACCOUNT
    if not st.session_state.get('logged_in', False):
        mode = st.radio("Action", ["Login", "Register"], horizontal=True)
        if mode == "Login":
            u = st.text_input("Username", key="login_u")
            p = st.text_input("Password", type="password", key="login_p")
            if st.button("Sign In"):
                db = st.session_state.users_db
                match = db[(db['Username'] == u) & (db['Password'] == p)]
                if not match.empty:
                    st.session_state.logged_in, st.session_state.current_user = True, u
                    st.session_state.user_role, st.session_state.user_status = match.iloc[0]['Role'], match.iloc[0]['Status']
                    st.rerun()
                else: st.error("Invalid credentials.")
        else:
            r_name = st.text_input("Full Name *", key="reg_name")
            r_user = st.text_input("Username *", key="reg_u")
            r_pass = st.text_input("Password *", type="password", key="reg_p")
            if st.button("Create Account"):
                if r_name.strip() and r_user.strip() and r_pass.strip():
                    new_user = {"Username": r_user, "Password": r_pass, "Role": "Trial", "Status": "Free", "Name": r_name}
                    st.session_state.users_db = pd.concat([st.session_state.users_db, pd.DataFrame([new_user])], ignore_index=True)
                    st.session_state.users_db.to_csv(DB_FILE, index=False)
                    st.success("✅ Registered! Switch to Login.")
                else: st.error("Fill required fields.")
    else:
        st.button("Sign Out", on_click=lambda: st.session_state.update({"logged_in": False}))

# --- 7. FOOTER RENDERING ---
footer_logo_html = f'<img src="data:image/png;base64,{logo_uday_b64}" class="footer-logo">' if logo_uday_b64 else ""
st.markdown(f"""
    <div class="footer-container">
        <div class="footer-line1">Sponsored By {footer_logo_html} <span class="name-highlight">Uday Mondal</span> | Consultant Advocate</div>
        <div class="footer-line2">Powered & Created by <span class="dev-highlight">Debasish Biswas</span> | Professional Tally Automation</div>
    </div>
""", unsafe_allow_html=True)
