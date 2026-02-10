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

# --- 2. SESSION STATE (DATABASE & PROFILE) ---
if 'users_db' not in st.session_state:
    st.session_state.users_db = pd.DataFrame([
        {"Username": "admin", "Password": "123", "Role": "Admin", "Pic": None},
        {"Username": "uday", "Password": "123", "Role": "User", "Pic": None}
    ])

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.current_user = None
    st.session_state.show_settings = False

# --- 3. CSS (PROFILE BUTTON & HIGH VISIBILITY) ---
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
        .stApp { background-color: #0056D2; }
        
        /* Fixed Nav Bar visibility */
        .stTabs {
            background-color: #0056D2;
            padding-top: 10px;
            position: sticky;
            top: 0;
            z-index: 1000;
        }
        .stTabs [data-baseweb="tab"] { color: #FFFFFF !important; font-weight: 600; }
        .stTabs [aria-selected="true"] { background-color: #FFFFFF !important; color: #0056D2 !important; border-radius: 8px; }

        /* Profile Header Area */
        .profile-header {
            display: flex;
            justify-content: flex-end;
            padding: 10px 20px;
            background: rgba(255,255,255,0.1);
        }

        /* White text for visibility */
        h1, h2, h3, p, label, .stMarkdown { color: #FFFFFF !important; }
        
        /* Pinned Footer */
        .footer {
            position: fixed;
            left: 0;
            bottom: 0;
            width: 100%;
            background-color: #FFFFFF;
            text-align: center;
            padding: 10px;
            z-index: 2000;
            border-top: 1px solid #ddd;
        }
        .footer p, .footer b { color: #333 !important; margin: 0; }
        
        div[data-testid="stButton"] button {
            background-color: #66E035;
            color: #0056D2;
            border-radius: 50px;
            font-weight: 700;
            border: none;
        }
        header {visibility: hidden;}
        .main .block-container { padding-bottom: 100px; }
    </style>
""", unsafe_allow_html=True)

# --- 4. LOGIC FUNCTIONS ---
def get_img_as_base64(file):
    try:
        if isinstance(file, str):
            with open(file, "rb") as f: return base64.b64encode(f.read()).decode()
        else:
            return base64.b64encode(file.getvalue()).decode()
    except: return None

# --- 5. TOP RIGHT PROFILE AREA ---
if st.session_state.logged_in:
    col_p1, col_p2 = st.columns([10, 1])
    with col_p2:
        # Check for user profile pic
        user_data = st.session_state.users_db[st.session_state.users_db['Username'] == st.session_state.current_user].iloc[0]
        if user_data['Pic']:
            st.image(user_data['Pic'], width=50)
        else:
            if st.button("👤 Profile"):
                st.session_state.show_settings = not st.session_state.show_settings
                st.rerun()

# --- 6. MAIN APP CONTENT ---
tabs = st.tabs(["Home", "Solutions", "Pricing", "Login", "Register"])

# TAB 1: HOME (WORKSPACE OR SETTINGS)
with tabs[0]:
    if st.session_state.logged_in:
        if st.session_state.show_settings:
            st.markdown("## ⚙️ Account Settings")
            new_pic = st.file_uploader("Update Profile Picture", type=['png', 'jpg'])
            new_pass = st.text_input("Change Password", type="password")
            
            if st.button("Save Changes"):
                idx = st.session_state.users_db[st.session_state.users_db['Username'] == st.session_state.current_user].index[0]
                if new_pic:
                    st.session_state.users_db.at[idx, 'Pic'] = new_pic
                if new_pass:
                    st.session_state.users_db.at[idx, 'Password'] = new_pass
                st.success("Profile Updated!")
                st.session_state.show_settings = False
                st.rerun()
                
            if st.button("← Back to Workspace"):
                st.session_state.show_settings = False
                st.rerun()
        else:
            st.markdown(f"<h1>Welcome back, {st.session_state.current_user}!</h1>", unsafe_allow_html=True)
            st.markdown("### 🛠️ Converter Tool (Full Access Enabled)")
            # [Converter logic from previous steps go here]
            st.file_uploader("Upload Bank Statement", type=['pdf', 'xlsx'])
    else:
        st.markdown('<h1>Perfecting the Science of Data Extraction</h1>', unsafe_allow_html=True)
        st.info("👋 Access Restricted. Please Sign In to use the tools.")

# TAB 4: LOGIN (FOR ADMIN/USER ACCESS)
with tabs[3]:
    st.markdown("## 🔐 Sign In")
    l_u = st.text_input("Username", key="l_u")
    l_p = st.text_input("Password", type="password", key="l_p")
    if st.button("Login"):
        db = st.session_state.users_db
        if ((db['Username'] == l_u) & (db['Password'] == l_p)).any():
            st.session_state.logged_in = True
            st.session_state.current_user = l_u
            st.success("Access Granted!")
            st.rerun()
        else:
            st.error("Invalid Login.")

# --- 7. PINNED FOOTER ---
try: u_logo = get_img_as_base64("logo 1.png")
except: u_logo = None
u_html = f'<img src="data:image/png;base64,{u_logo}" width="20" style="vertical-align:middle; margin-right:5px;">' if u_logo else ""

st.markdown(f"""
    <div class="footer">
        <p>Sponsored By {u_html} <b>Uday Mondal</b> | Consultant Advocate</p>
        <p style="font-size: 11px; color: #666 !important;">Powered & Created by <b>Debasish Biswas</b></p>
    </div>
""", unsafe_allow_html=True)
