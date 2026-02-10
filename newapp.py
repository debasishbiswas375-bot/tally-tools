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

# --- 2. SESSION STATE (FIXED: Always initialize 'Pic' to avoid KeyError) ---
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

# --- 3. REFINED CSS (FIXED: Visible Tabs & No White Zones) ---
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
        
        .stApp { background-color: #0056D2; }

        /* FIXED NAVIGATION - Standard padding to keep tabs visible */
        .stTabs {
            background-color: #0056D2;
            padding-top: 10px;
            z-index: 1000;
            border-bottom: 1px solid rgba(255,255,255,0.2);
        }
        
        .stTabs [data-baseweb="tab-list"] { 
            gap: 15px; 
            justify-content: flex-end; 
            padding-right: 20px; 
        }
        
        .stTabs [data-baseweb="tab"] { 
            color: #FFFFFF !important; 
            font-weight: 600; 
            font-size: 1rem;
            border-bottom: none !important;
        }
        
        .stTabs [aria-selected="true"] { 
            background-color: #FFFFFF !important; 
            color: #0056D2 !important; 
            border-radius: 8px 8px 0 0; 
        }

        /* TEXT READABILITY */
        h1, h2, h3, p, span, label, .stMarkdown { color: #FFFFFF !important; }
        
        /* PINNED FOOTER */
        .footer {
            position: fixed;
            left: 0;
            bottom: 0;
            width: 100%;
            background-color: #FFFFFF;
            text-align: center;
            padding: 10px;
            z-index: 2000;
            border-top: 1px solid #E2E8F0;
        }
        .footer p, .footer b { color: #1E293B !important; margin: 0; }

        /* Hide Default Streamlit Header */
        header {visibility: hidden;}
        #MainMenu {visibility: hidden;}
        .main .block-container { padding-bottom: 120px; }
        
        /* Fixed Profile Button Styling */
        div.stButton > button:first-child {
            border-radius: 50px;
            font-weight: 700;
        }
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

# --- 5. MAIN NAVIGATION ---
# Home, Solutions, Pricing, Login, Register
tabs = st.tabs(["Home", "Solutions", "Pricing", "Login", "Register"])

with tabs[0]: # HOME
    # Top Profile Header (Only if logged in)
    if st.session_state.logged_in:
        p_col1, p_col2 = st.columns([12, 1])
        with p_col2:
            if st.button("👤 Profile"):
                st.session_state.show_settings = not st.session_state.show_settings
                st.rerun()

    if st.session_state.logged_in:
        if st.session_state.show_settings:
            st.subheader("⚙️ Account Settings")
            new_pass = st.text_input("Change Password", type="password")
            if st.button("Save Profile"):
                idx = st.session_state.users_db[st.session_state.users_db['Username'] == st.session_state.current_user].index[0]
                if new_pass: st.session_state.users_db.at[idx, 'Password'] = new_pass
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
                c1, c2 = st.columns(2, gap="large")
                with c1:
                    with st.container(border=True):
                        st.markdown("#### Upload Tally Master")
                        up_html = st.file_uploader("master.html", type=['html'])
                        ledgers = get_ledger_names(up_html) if up_html else ["Cash", "Bank"]
                        st.selectbox("Select Bank Ledger", ledgers)
                with c2:
                    with st.container(border=True):
                        st.markdown("#### Upload Statement")
                        st.file_uploader("Bank Statement", type=['pdf', 'xlsx'])
                        st.button("🚀 Process & Generate XML")
            else:
                st.markdown("### ⏳ Trial Mode")
                st.warning("Please contact the Admin for Full Access.")
    else:
        st.markdown('<h1>Perfecting the Science of Data Extraction</h1>', unsafe_allow_html=True)
        st.info("👋 Use the **Login** or **Register** tabs to begin processing your files.")

# --- SHARED CONTENT ---
with tabs[1]:
    st.markdown("## 🌟 Our Solutions")
    st.write("Bank Statement to Tally XML Conversion with 99% Accuracy.")

with tabs[2]:
    st.markdown("## 💰 Pricing")
    st.write("Trial: Free | Full Access: Contact Admin")

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
            st.session_state.user_role = user_match.iloc[0]['Role']
            st.rerun()
        else: st.error("Invalid Username or Password.")

with tabs[4]: # REGISTER
    st.markdown("## 🚀 Register")
    r_u = st.text_input("New Username", key="r_u")
    r_p = st.text_input("New Password", type="password", key="r_p")
    if st.button("Register Now"):
        if r_u in st.session_state.users_db['Username'].values:
            st.error("Username already exists!")
        else:
            new_u = pd.DataFrame([{"Username": r_u, "Password": r_p, "Role": "Trial", "Pic": None}])
            st.session_state.users_db = pd.concat([st.session_state.users_db, new_u], ignore_index=True)
            st.success("Registered as Trial user! Please Login.")

# --- 6. PINNED GLOBAL FOOTER ---
try: 
    uday_logo_b64 = get_img_as_base64("logo 1.png")
    uday_logo_html = f'<img src="data:image/png;base64,{uday_logo_b64}" width="20" style="vertical-align:middle;">' if uday_logo_b64 else ""
except: uday_logo_html = ""

st.markdown(f"""
    <div class="footer">
        <p>Sponsored By {uday_logo_html} <b>Uday Mondal</b> | Consultant Advocate</p>
        <p style="font-size: 11px; margin-top: 4px; color: #64748B !important;">
            Powered & Created by <b>Debasish Biswas</b>
        </p>
    </div>
""", unsafe_allow_html=True)
