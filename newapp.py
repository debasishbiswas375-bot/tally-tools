import streamlit as st
import pandas as pd
from bs4 import BeautifulSoup
import io
from PIL import Image

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Accounting Expert",
    page_icon="logo.png",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 2. SESSION STATE (STABILIZED) ---
if 'users_db' not in st.session_state:
    st.session_state.users_db = pd.DataFrame([
        {"Username": "admin", "Password": "123", "Role": "Admin", "Status": "Paid", "Pic": None},
        {"Username": "uday", "Password": "123", "Role": "Trial", "Status": "Free", "Pic": None}
    ])

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.current_user = None
    st.session_state.user_role = None
    st.session_state.show_profile = False

# --- 3. CUSTOM CSS ---
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
        .stApp { background-color: #0056D2; }

        /* NAVIGATION TABS */
        .stTabs [data-baseweb="tab-list"] { gap: 20px; justify-content: flex-end; }
        .stTabs [data-baseweb="tab"] { color: #FFFFFF !important; font-weight: 600; }
        .stTabs [aria-selected="true"] { background-color: #FFFFFF !important; color: #0056D2 !important; border-radius: 8px 8px 0 0; }

        /* INPUT VISIBILITY */
        input, .stSelectbox div, [data-testid="stFileUploader"] * { color: #000000 !important; }
        label { color: #FFFFFF !important; font-weight: 600 !important; }
        h1, h2, h3, p, .stMarkdown { color: #FFFFFF !important; }

        /* PRICING CARDS FIX */
        .price-card {
            background-color: #FFFFFF;
            padding: 20px;
            border-radius: 15px;
            color: #1E293B !important;
            min-height: 200px;
            border-top: 5px solid #66E035;
        }
        .price-card h4, .price-card li, .price-card b { color: #1E293B !important; }

        /* PROFILE STYLING */
        .profile-box {
            background: rgba(255, 255, 255, 0.1);
            padding: 20px;
            border-radius: 15px;
            border: 1px solid rgba(255, 255, 255, 0.2);
        }

        /* BUTTONS */
        div.stButton > button {
            background-color: #66E035 !important;
            color: #0056D2 !important;
            border-radius: 50px !important;
            font-weight: 700 !important;
        }

        header {visibility: hidden;}
        .footer {
            position: fixed; left: 0; bottom: 0; width: 100%;
            background-color: #FFFFFF; text-align: center;
            padding: 10px; z-index: 2000;
        }
        .footer p, .footer b { color: #1E293B !important; margin: 0; }
    </style>
""", unsafe_allow_html=True)

# --- 4. LOGIC FUNCTIONS ---
def get_ledger_names(html_file):
    try:
        soup = BeautifulSoup(html_file, 'html.parser')
        ledgers = [td.get_text(strip=True) for td in soup.find_all('td') if td.get_text(strip=True)]
        return sorted(list(set(ledgers)))
    except: return ["Cash", "Bank"]

# --- 5. MAIN NAVIGATION ---
tabs = st.tabs(["Home", "Solutions", "Pricing", "Account"])

with tabs[0]: # HOME
    if st.session_state.logged_in:
        st.markdown(f"<h1>Welcome back, {st.session_state.current_user}!</h1>", unsafe_allow_html=True)
        
        if st.session_state.user_role == "Admin":
            st.markdown("### 🛠️ Converter Tool (Full Access)")
            col1, col2 = st.columns(2, gap="large")
            with col1:
                with st.container(border=True):
                    st.markdown("#### 1. Settings")
                    st.selectbox("Select Bank Format", ["SBI", "HDFC", "ICICI"])
                    up_html = st.file_uploader("Upload Tally Master", type=['html'])
                    ledgers = get_ledger_names(up_html) if up_html else ["Cash", "Bank"]
                    st.selectbox("Select Bank Ledger", ledgers)
            with col2:
                with st.container(border=True):
                    st.markdown("#### 2. Process")
                    st.file_uploader("Drop Statement", type=['pdf', 'xlsx'])
                    st.button("🚀 Process & Generate XML")
        else:
            st.warning("⚠️ Trial Mode: Please contact Admin for Full Access.")
    else:
        st.markdown('<h1>Perfecting the Science of Data Extraction</h1>', unsafe_allow_html=True)
        st.info("👋 Please go to the **Account** tab to Sign In or Register.")

with tabs[1]: # SOLUTIONS
    st.markdown("## 🚀 Our Solutions")
    st.write("- Bank Statement to Tally XML Converter")
    st.write("- Auto-ledger mapping via HTML Master files")

with tabs[2]: # PRICING
    st.markdown("## 💰 Plans")
    p1, p2 = st.columns(2)
    with p1:
        st.markdown('<div class="price-card"><h4>Free Plan</h4><ul><li>Unlimited Previews</li><li>No XML Export</li></ul><b>Price: ₹0</b></div>', unsafe_allow_html=True)
    with p2:
        st.markdown('<div class="price-card"><h4>Paid Plan</h4><ul><li>Full XML Export</li><li>Priority Support</li></ul><b>Contact for Price</b></div>', unsafe_allow_html=True)

with tabs[3]: # ACCOUNT (INTEGRATED LOGIN/REGISTER/PROFILE)
    if not st.session_state.logged_in:
        choice = st.radio("Choose Action", ["Login", "Register"], horizontal=True)
        
        if choice == "Login":
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            if st.button("Sign In"):
                db = st.session_state.users_db
                user = db[(db['Username'] == u) & (db['Password'] == p)]
                if not user.empty:
                    st.session_state.logged_in = True
                    st.session_state.current_user = u
                    st.session_state.user_role = user.iloc[0]['Role']
                    st.rerun()
                else: st.error("Invalid credentials")
        else:
            new_u = st.text_input("New Username")
            new_p = st.text_input("New Password", type="password")
            if st.button("Create Account"):
                new_data = {"Username": new_u, "Password": new_p, "Role": "Trial", "Status": "Free", "Pic": None}
                st.session_state.users_db = pd.concat([st.session_state.users_db, pd.DataFrame([new_data])], ignore_index=True)
                st.success("Account Created! You can now login.")
    
    else:
        # PROFILE SECTION
        st.markdown("## 👤 Your Profile")
        user_idx = st.session_state.users_db[st.session_state.users_db['Username'] == st.session_state.current_user].index[0]
        user_data = st.session_state.users_db.iloc[user_idx]

        with st.container():
            col_img, col_info = st.columns([1, 3])
            
            with col_img:
                if user_data['Pic'] is not None:
                    st.image(user_data['Pic'], width=150)
                else:
                    st.write("No Profile Picture")
                
                new_pic = st.file_uploader("Update Picture", type=['png', 'jpg', 'jpeg'])
                if new_pic:
                    st.session_state.users_db.at[user_idx, 'Pic'] = new_pic
                    st.rerun()

            with col_info:
                st.markdown(f"### {user_data['Username']}")
                status_color = "#66E035" if user_data['Status'] == "Paid" else "#FF4B4B"
                st.markdown(f"**Subscription Status:** <span style='color:{status_color}; font-weight:bold;'>{user_data['Status']} User</span>", unsafe_allow_html=True)
                st.markdown(f"**Role:** {user_data['Role']}")
                
                if st.button("Logout"):
                    st.session_state.logged_in = False
                    st.rerun()

# --- 6. FOOTER ---
st.markdown("""
    <div class="footer">
        <p>Sponsored By <b>Uday Mondal</b> | Powered & Created by <b>Debasish Biswas</b></p>
    </div>
""", unsafe_allow_html=True)
