import streamlit as st
import pandas as pd
from bs4 import BeautifulSoup
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
        {
            "Username": "admin", "Password": "123", "Role": "Admin", 
            "Status": "Paid", "Pic": None, "Name": "Admin User", 
            "Mobile": "0000000000", "Email": "admin@example.com", "Company": "Master Corp"
        },
        {
            "Username": "uday", "Password": "123", "Role": "Trial", 
            "Status": "Free", "Pic": None, "Name": "Uday Mondal", 
            "Mobile": "9876543210", "Email": "uday@example.com", "Company": "N/A"
        }
    ])

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.current_user = None
    st.session_state.user_role = None

# --- 3. UNIFIED CUSTOM CSS ---
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
        .stApp { background-color: #0056D2; }

        /* NAVIGATION TABS */
        .stTabs [data-baseweb="tab-list"] { gap: 20px; justify-content: flex-end; }
        .stTabs [data-baseweb="tab"] { color: #FFFFFF !important; font-weight: 600; font-size: 16px; }
        .stTabs [aria-selected="true"] { background-color: #FFFFFF !important; color: #0056D2 !important; border-radius: 8px 8px 0 0; }

        /* INPUTS & SELECTBOXES */
        input, .stSelectbox div, [data-testid="stFileUploader"] * { color: #000000 !important; }
        label { color: #FFFFFF !important; font-weight: 600 !important; }
        h1, h2, h3, p, .stMarkdown { color: #FFFFFF !important; }

        /* UNIFIED WHITE CARDS FOR ALL TABS */
        .content-card {
            background-color: #FFFFFF;
            padding: 25px;
            border-radius: 15px;
            color: #1E293B !important;
            margin-bottom: 20px;
            border-top: 8px solid #66E035;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        }
        .content-card h4, .content-card p, .content-card li, .content-card b { color: #1E293B !important; }

        /* THE GREEN & BLUE PILL BUTTON */
        div.stButton > button {
            background-color: #66E035 !important;
            color: #0056D2 !important;
            border-radius: 50px !important;
            font-weight: 700 !important;
            padding: 0.5rem 2.5rem !important;
            border: none !important;
            transition: all 0.2s ease;
        }
        div.stButton > button:hover {
            transform: scale(1.05);
            box-shadow: 0 4px 10px rgba(0,0,0,0.2);
            color: #0056D2 !important;
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
            col1, col2 = st.columns(2, gap="large")
            with col1:
                with st.container(border=True):
                    st.markdown("#### 1. Settings")
                    st.selectbox("Select Bank Format", ["SBI", "HDFC", "ICICI", "Other"])
                    up_html = st.file_uploader("Upload Tally Master", type=['html'])
                    ledgers = get_ledger_names(up_html) if up_html else ["Cash", "Bank"]
                    st.selectbox("Select Bank Ledger", ledgers)
            with col2:
                with st.container(border=True):
                    st.markdown("#### 2. Process")
                    st.file_uploader("Drop Bank Statement", type=['pdf', 'xlsx'])
                    st.button("🚀 Process & Generate XML")
        else:
            st.warning("⚠️ Trial Mode: Please contact Admin to upgrade.")
    else:
        st.markdown('<h1>Perfecting the Science of Data Extraction</h1>', unsafe_allow_html=True)
        st.info("👋 Visit the **Account** tab to Sign In or Register.")

with tabs[1]: # SOLUTIONS
    st.markdown("## 🚀 Our Solutions")
    st.markdown("""
        <div class="content-card">
            <h4>Bank to Tally Converter</h4>
            <p>Seamlessly transform bank PDF/Excel files into Tally Prime XML formats with 100% accuracy.</p>
        </div>
        <div class="content-card">
            <h4>Ledger Sync</h4>
            <p>Import your Tally ledger masters directly to ensure perfect accounting mapping.</p>
        </div>
    """, unsafe_allow_html=True)

with tabs[2]: # PRICING
    st.markdown("## 💰 Pricing Plans")
    p1, p2 = st.columns(2)
    with p1:
        st.markdown("""
            <div class="content-card" style="border-top-color: #CBD5E1;">
                <h4>Trial Plan</h4>
                <ul><li>✅ Unlimited Previews</li><li>❌ No XML Export</li></ul>
                <b>Price: Free</b>
            </div>
        """, unsafe_allow_html=True)
        st.button("Get Started", key="btn_trial")
    with p2:
        st.markdown("""
            <div class="content-card">
                <h4>Professional Plan</h4>
                <ul><li>✅ Full XML Export</li><li>✅ All Bank Formats</li></ul>
                <b>Contact Admin for Price</b>
            </div>
        """, unsafe_allow_html=True)
        st.button("Contact Us", key="btn_pro")

with tabs[3]: # ACCOUNT
    if not st.session_state.logged_in:
        mode = st.radio("Choose Action", ["Login", "Register"], horizontal=True)
        if mode == "Login":
            st.text_input("Username", key="l_u")
            st.text_input("Password", type="password", key="l_p")
            if st.button("Sign In"):
                # Simplified for demonstration
                st.session_state.logged_in = True
                st.rerun()
        else:
            st.text_input("Full Name *")
            st.text_input("Mobile *")
            st.text_input("Username *")
            st.text_input("Password *", type="password")
            st.text_input("Company (Optional)")
            st.button("Create Account")
    else:
        st.markdown("## 👤 Your Profile")
        with st.container():
            st.markdown("""
                <div class="content-card">
                    <h4>Subscription Details</h4>
                    <p><b>Status:</b> <span style="color:#66E035;">Paid User</span></p>
                    <p><b>Role:</b> Administrator</p>
                </div>
            """, unsafe_allow_html=True)
            if st.button("Logout"):
                st.session_state.logged_in = False
                st.rerun()

# --- 6. FOOTER ---
st.markdown('<div class="footer"><p>Sponsored By <b>Uday Mondal</b> | Powered & Created by <b>Debasish Biswas</b></p></div>', unsafe_allow_html=True)
