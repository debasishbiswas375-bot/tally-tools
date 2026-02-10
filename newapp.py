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

# --- 3. CUSTOM CSS (FIXED CONTRAST & VISIBILITY) ---
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
        
        .stApp { background-color: #0056D2; }

        /* NAVIGATION TABS */
        .stTabs {
            background-color: #0056D2;
            padding-top: 10px;
            z-index: 1000;
            border-bottom: 1px solid rgba(255,255,255,0.2);
        }
        .stTabs [data-baseweb="tab-list"] { gap: 15px; justify-content: flex-end; padding-right: 20px; }
        .stTabs [data-baseweb="tab"] { color: #FFFFFF !important; font-weight: 600; border: none !important; }
        .stTabs [aria-selected="true"] { background-color: #FFFFFF !important; color: #0056D2 !important; border-radius: 8px 8px 0 0; }

        /* INPUTS & UPLOADERS (FORCING BLACK TEXT) */
        [data-testid="stFileUploader"] * { color: #000000 !important; }
        [data-testid="stFileUploaderDropzone"] div { color: #000000 !important; font-weight: 500 !important; }
        input, .stTextInput input, .stSelectbox div, .stSelectbox span { color: #000000 !important; font-weight: 500 !important; }

        label { color: #FFFFFF !important; font-weight: 600 !important; }
        h1, h2, h3, p, span, .stMarkdown { color: #FFFFFF !important; }

        /* PRICING CARDS (HIGH CONTRAST FIX) */
        .price-card {
            background-color: #FFFFFF;
            padding: 25px;
            border-radius: 15px;
            margin-bottom: 20px;
            min-height: 220px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .price-card h4 { color: #0056D2 !important; margin-top: 0; font-weight: 800; }
        .price-card ul { color: #1E293B !important; list-style-type: none; padding-left: 0; }
        .price-card li { margin-bottom: 12px; font-weight: 500; font-size: 1.1em; }
        .price-card b { color: #0056D2; font-size: 1.1em; }

        /* PINNED FOOTER */
        .footer {
            position: fixed; left: 0; bottom: 0; width: 100%;
            background-color: #FFFFFF; text-align: center;
            padding: 10px; z-index: 2000; border-top: 1px solid #E2E8F0;
        }
        .footer p, .footer b { color: #1E293B !important; margin: 0; }

        /* BUTTONS */
        div.stButton > button {
            background-color: #66E035 !important;
            color: #0056D2 !important;
            border-radius: 50px !important;
            font-weight: 700 !important;
            border: none !important;
        }

        header {visibility: hidden;}
        #MainMenu {visibility: hidden;}
        .main .block-container { padding-bottom: 120px; }
    </style>
""", unsafe_allow_html=True)

# --- 4. LOGIC FUNCTIONS ---
def get_ledger_names(html_file):
    try:
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
                    st.session_state.users_db.at[idx, 'Password'] = new_pass
                st.success("Profile Updated!")
                st.session_state.show_settings = False
                st.rerun()
            if st.button("Logout"):
                st.session_state.logged_in = False
                st.session_state.current_user = None
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
                        up_html = st.file_uploader("Upload Tally Master (master.html)", type=['html'])
                        ledgers = get_ledger_names(up_html) if up_html else ["Cash", "Bank"]
                        st.selectbox("Select Bank Ledger", ledgers)
                        st.selectbox("Select Default Party", ledgers)
                with col2:
                    with st.container(border=True):
                        st.markdown("#### 📂 2. Upload & Convert")
                        st.file_uploader("Drop your Bank Statement here", type=['pdf', 'xlsx'])
                        if st.button("🚀 Process & Generate XML"):
                            st.success("✅ Conversion Process Started! Check logs below.")
            else:
                st.warning("⚠️ Trial Mode: Please contact Admin for Full Access to XML Export features.")
    else:
        st.markdown('<h1>Perfecting the Science of Data Extraction</h1>', unsafe_allow_html=True)
        st.info("👋 Welcome! Please use the **Login** tab to access the tool or **Register** for a trial.")

with tabs[1]: # SOLUTIONS
    st.markdown("## 🚀 Our Solutions")
    st.markdown("""
    ### 🏦 Bank to Tally XML
    Convert complex PDF and Excel bank statements into structured Tally XML format in seconds.
    
    ### 📋 Ledger Auto-Mapping
    By uploading your `master.html` from Tally, our system automatically maps your bank entries to your existing ledgers.
    
    ### 🛡️ Secure & Offline
    Your data stays in the browser session. We prioritize the security of your financial information.
    """)

with tabs[2]: # PRICING
    st.markdown("## 💰 Pricing & Plans")
    col_a, col_b = st.columns(2)
    
    with col_a:
        st.markdown("""
            <div class="price-card" style="border-left: 10px solid #CBD5E1;">
                <h4>Trial Plan</h4>
                <ul>
                    <li>✅ Unlimited previews</li>
                    <li>❌ Restricted XML Export</li>
                    <li>✅ Basic Support</li>
                    <li><b>Price: Free</b></li>
                </ul>
            </div>
        """, unsafe_allow_html=True)

    with col_b:
        st.markdown("""
            <div class="price-card" style="border-left: 10px solid #66E035;">
                <h4>Professional Plan</h4>
                <ul>
                    <li>✅ Full XML Generation</li>
                    <li>✅ All Bank Formats supported</li>
                    <li>✅ Priority Admin Support</li>
                    <li><b>Contact Admin for Access</b></li>
                </ul>
            </div>
        """, unsafe_allow_html=True)

with tabs[3]: # LOGIN
    if st.session_state.logged_in:
        st.success(f"You are already logged in as **{st.session_state.current_user}**.")
    else:
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

with tabs[4]: # REGISTER
    st.markdown("## 📝 Create Account")
    new_u = st.text_input("Choose Username", key="reg_u")
    new_p = st.text_input("Choose Password", type="password", key="reg_p")
    if st.button("Register Now"):
        if new_u and new_p:
            new_row = {"Username": new_u, "Password": new_p, "Role": "Trial", "Pic": None}
            st.session_state.users_db = pd.concat([st.session_state.users_db, pd.DataFrame([new_row])], ignore_index=True)
            st.success("✅ Registration Successful! Please switch to the **Login** tab to sign in.")
        else:
            st.error("Please fill in both fields.")

# --- 6. FOOTER ---
st.markdown(f"""
    <div class="footer">
        <p>Sponsored By <b>Uday Mondal</b> | Powered & Created by <b>Debasish Biswas</b></p>
    </div>
""", unsafe_allow_html=True)
