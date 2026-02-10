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

# --- 3. CSS STYLING (The Visibility Fix) ---
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
        
        /* Background */
        .stApp { background-color: #0056D2; }

        /* HEADER TEXTS */
        h1, h2, h3, h4, .stMarkdown p { color: #FFFFFF !important; }

        /* TARGETING THE 2 UPLOADER LABELS ONLY (White) */
        [data-testid="stFileUploader"] label {
            color: #FFFFFF !important;
            font-weight: 600 !important;
        }

        /* SELECTBOX LABELS (White) */
        [data-testid="stSelectbox"] label {
            color: #FFFFFF !important;
        }

        /* INTERNAL BOX TEXT (Keep Black for visibility against white) */
        [data-testid="stFileUploaderDropzone"] div, 
        [data-testid="stFileUploaderDropzone"] span,
        [data-testid="stFileUploader"] button p {
            color: #000000 !important;
            font-weight: 500 !important;
        }
        
        /* Selectbox and Input text inside the boxes (Black) */
        input, .stTextInput input, .stSelectbox div, .stSelectbox span {
            color: #000000 !important;
            font-weight: 500 !important;
        }

        /* NAVIGATION TABS */
        .stTabs [data-baseweb="tab-list"] { gap: 15px; justify-content: flex-end; padding-right: 20px; }
        .stTabs [data-baseweb="tab"] { color: #FFFFFF !important; font-weight: 600; }
        .stTabs [aria-selected="true"] { background-color: #FFFFFF !important; color: #0056D2 !important; border-radius: 8px 8px 0 0; }

        /* PINNED FOOTER */
        .footer {
            position: fixed; left: 0; bottom: 0; width: 100%;
            background-color: #FFFFFF; text-align: center;
            padding: 10px; z-index: 2000; border-top: 1px solid #E2E8F0;
        }
        .footer p, .footer b { color: #1E293B !important; margin: 0; }

        /* PROCESS BUTTON */
        div.stButton > button {
            background-color: #66E035 !important;
            color: #0056D2 !important;
            border-radius: 50px !important;
            font-weight: 700 !important;
            width: 100%;
        }

        header {visibility: hidden;}
        #MainMenu {visibility: hidden;}
        .main .block-container { padding-bottom: 120px; }
    </style>
""", unsafe_allow_html=True)

# --- 4. LOGIC FUNCTIONS ---
def get_ledger_names(html_file):
    try:
        # Extract names from Tally Master HTML
        soup = BeautifulSoup(html_file, 'html.parser')
        ledgers = [td.get_text(strip=True) for td in soup.find_all('td') if td.get_text(strip=True)]
        return sorted(list(set(ledgers)))
    except: 
        return ["Cash", "Bank", "Suspense A/c"]

# --- 5. MAIN NAVIGATION ---
tabs = st.tabs(["Home", "Solutions", "Pricing", "Login", "Register"])

with tabs[0]: # HOME
    if st.session_state.logged_in:
        p_col1, p_col2 = st.columns([12, 1.5])
        with p_col2:
            if st.button("👤 Profile"):
                st.session_state.show_settings = not st.session_state.show_settings
                st.rerun()

        if st.session_state.show_settings:
            st.markdown("## ⚙️ Account Settings")
            new_pass = st.text_input("Change Password", type="password")
            if st.button("Save Profile"):
                idx = st.session_state.users_db[st.session_state.users_db['Username'] == st.session_state.current_user].index[0]
                if new_pass:
                    st.session_state.users_db.at(idx, 'Password'] = new_pass
                st.success("Profile Updated!")
                st.session_state.show_settings = False
                st.rerun()
            if st.button("Logout"):
                st.session_state.logged_in = False
                st.rerun()
        else:
            st.markdown(f"<h1>Welcome back, {st.session_state.current_user}!</h1>", unsafe_allow_html=True)
            if st.session_state.user_role == "Admin":
                st.markdown("### 🛠️ Converter Tool (Full Access)")
                col1, col2 = st.columns(2, gap="large")
                with col1:
                    with st.container(border=True):
                        st.markdown("#### 🛠️ 1. Settings & Mapping")
                        st.selectbox("Select Bank Format", ["SBI", "HDFC", "ICICI", "Other"])
                        
                        # Label 1 (White via CSS)
                        up_html = st.file_uploader("Upload Tally Master (master.html)", type=['html'])
                        
                        ledgers = get_ledger_names(up_html) if up_html else ["Cash", "Bank"]
                        st.selectbox("Select Bank Ledger", ledgers)
                        st.selectbox("Select Default Party", ledgers)
                with col2:
                    with st.container(border=True):
                        st.markdown("#### 📂 2. Upload & Convert")
                        
                        # Label 2 (White via CSS)
                        st.file_uploader("Drop your Bank Statement here", type=['pdf', 'xlsx'])
                        
                        st.button("🚀 Process & Generate XML")
            else:
                st.warning("⚠️ Trial Mode: Please contact Admin for Full Access.")
    else:
        st.markdown('<h1>Perfecting the Science of Data Extraction</h1>', unsafe_allow_html=True)
        st.info("👋 Use the Login tab to begin.")

with tabs[3]: # LOGIN
    st.markdown("## 🔐 Sign In")
    l_u = st.text_input("Username", key="login_u")
    l_p = st.text_input("Password", type="password", key="login_p")
    if st.button("Sign In"):
        db = st.session_state.users_db
        user_match = db[(db['Username'] == l_u) & (db['Password'] == l_p)]
        if not user_match.empty:
            st.session_state.logged_in = True
            st.session_state.current_user = l_u
            st.session_state.user_role = user_match.iloc[0]['Role']
            st.rerun()
        else: 
            st.error("Invalid credentials.")

# --- 6. FOOTER ---
st.markdown(f"""
    <div class="footer">
        <p>Sponsored By <b>Uday Mondal</b> | Powered & Created by <b>Debasish Biswas</b></p>
    </div>
""", unsafe_allow_html=True)
