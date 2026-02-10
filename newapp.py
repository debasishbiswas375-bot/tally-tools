import streamlit as st
import pandas as pd
from bs4 import BeautifulSoup
import pdfplumber
import base64
import io
from PIL import Image

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Accounting Expert",
    page_icon="logo.png",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 2. SESSION STATE (FIXED: Auto-assign 'Trial' role to new users) ---
if 'users_db' not in st.session_state:
    st.session_state.users_db = pd.DataFrame([
        {"Username": "admin", "Password": "123", "Role": "Admin", "Pic": None},
        {"Username": "uday", "Password": "123", "Role": "Trial", "Pic": None}
    ])

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.current_user = None
    st.session_state.user_role = None
    st.session_state.show_settings = False

# --- 3. REFINED CSS ---
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
        .stApp { background-color: #0056D2; }
        .stTabs { background-color: #0056D2; padding-top: 10px; z-index: 1000; border-bottom: 1px solid rgba(255,255,255,0.2); }
        .stTabs [data-baseweb="tab-list"] { gap: 20px; justify-content: flex-end; padding-right: 40px; }
        .stTabs [data-baseweb="tab"] { color: #FFFFFF !important; font-weight: 600; padding: 10px 20px; }
        .stTabs [aria-selected="true"] { background-color: #FFFFFF !important; color: #0056D2 !important; border-radius: 8px; }
        h1, h2, h3, p, span, label, .stMarkdown { color: #FFFFFF !important; }
        .stTextInput label, .stSelectbox label, .stFileUploader label { color: #FFFFFF !important; font-weight: 600 !important; }
        .footer { position: fixed; left: 0; bottom: 0; width: 100%; background-color: #FFFFFF; text-align: center; padding: 12px; z-index: 2000; border-top: 1px solid #E2E8F0; }
        .footer p, .footer b { color: #1E293B !important; margin: 0; }
        div[data-testid="stButton"] button { background-color: #66E035; color: #0056D2; border-radius: 50px; font-weight: 700; border: none; }
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

def get_ledger_names(html_file):
    try:
        soup = BeautifulSoup(html_file, 'html.parser')
        ledgers = [td.get_text(strip=True) for td in soup.find_all('td') if td.get_text(strip=True)]
        return sorted(list(set(ledgers)))
    except: return ["Cash", "Bank", "Suspense A/c"]

# --- 5. TOP RIGHT PROFILE AREA ---
if st.session_state.logged_in:
    t_col1, t_col2 = st.columns([12, 1])
    with t_col2:
        user_row = st.session_state.users_db[st.session_state.users_db['Username'] == st.session_state.current_user].iloc[0]
        if user_row.get('Pic') is not None:
            st.image(user_row['Pic'], width=40)
        if st.button("👤 Profile"):
            st.session_state.show_settings = not st.session_state.show_settings; st.rerun()

# --- 6. MAIN NAVIGATION ---
tabs = st.tabs(["Home", "Solutions", "Pricing", "Login", "Register"])

with tabs[0]: # HOME
    if st.session_state.logged_in:
        if st.session_state.show_settings:
            st.subheader("⚙️ Profile Settings")
            new_pass = st.text_input("Change Password", type="password")
            if st.button("Save Profile"):
                idx = st.session_state.users_db[st.session_state.users_db['Username'] == st.session_state.current_user].index[0]
                if new_pass: st.session_state.users_db.at[idx, 'Password'] = new_pass
                st.success("Profile Updated!"); st.session_state.show_settings = False; st.rerun()
            if st.button("Logout"):
                st.session_state.logged_in = False; st.rerun()
        else:
            st.markdown(f"<h1>Welcome back, {st.session_state.current_user}!</h1>", unsafe_allow_html=True)
            
            # --- ACCESS CONTROL LOGIC ---
            if st.session_state.user_role == "Admin":
                st.markdown("### 🛠️ Converter Tool (Full Access Admin Mode)")
                c1, c2 = st.columns([1, 1.5], gap="large")
                with c1:
                    with st.container(border=True):
                        up_html = st.file_uploader("Upload Tally Master", type=['html'])
                        ledger_list = get_ledger_names(up_html) if up_html else ["Cash", "Bank"]
                        st.selectbox("Select Bank Ledger", ledger_list)
                with c2:
                    with st.container(border=True):
                        st.file_uploader("Upload Statement", type=['xlsx', 'pdf'])
                        st.button("🚀 Process & Generate XML")
            else:
                st.markdown("### ⏳ Trial Mode")
                st.warning("Your account is currently in Trial Mode. Please contact the Admin for Full Access.")
                st.info("Limited Preview of Data is available for Trial users.")
    else:
        st.markdown('<h1>Perfecting the Science of Data Extraction</h1>', unsafe_allow_html=True)
        st.info("👋 Use the **Login** tab to enable access.")

with tabs[1]: # SOLUTIONS
    st.markdown("## 🌟 Our Solutions")
    st.write("1. Bank Statement to Tally: Smart PDF/Excel parsing.")
    st.write("2. Master Ledger Sync: Auto-detect ledgers from Tally exports.")

with tabs[3]: # LOGIN
    st.markdown("## 🔐 Sign In")
    l_u = st.text_input("Username", key="l_u")
    l_p = st.text_input("Password", type="password", key="l_p")
    if st.button("Sign In"):
        db = st.session_state.users_db
        user_match = db[(db['Username'] == l_u) & (db['Password'] == l_p)]
        if not user_match.empty:
            st.session_state.logged_in = True
            st.session_state.current_user = l_u
            st.session_state.user_role = user_match.iloc[0]['Role'] # Sets the role during login
            st.rerun()
        else: st.error("Invalid Username or Password.")

with tabs[4]: # REGISTER (FIXED: Forces 'Trial' Role)
    st.markdown("## 🚀 Register Account")
    r_u = st.text_input("New Username", key="r_u")
    r_p = st.text_input("New Password", type="password", key="r_p")
    if st.button("Register Now"):
        if r_u in st.session_state.users_db['Username'].values:
            st.error("Username already exists!")
        else:
            # New users are ALWAYS created as 'Trial'
            new_user = pd.DataFrame([{"Username": r_u, "Password": r_p, "Role": "Trial", "Pic": None}])
            st.session_state.users_db = pd.concat([st.session_state.users_db, new_user], ignore_index=True)
            st.success("Account created as 'Trial'. Please Login.")

# --- 7. PINNED GLOBAL FOOTER ---
try: uday_logo = get_img_as_base64("logo 1.png")
except: uday_logo = None
uday_html = f'<img src="data:image/png;base64,{uday_logo}" width="20" style="vertical-align:middle; margin-right:5px;">' if uday_logo else ""

st.markdown(f"""
    <div class="footer">
        <p>Sponsored By {uday_html} <b>Uday Mondal</b> | Consultant Advocate</p>
        <p style="font-size: 11px; margin-top: 4px; color: #64748B !important;">Powered & Created by <b>Debasish Biswas</b></p>
    </div>
""", unsafe_allow_html=True)
