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

# --- 2. SESSION STATE (STABILIZED DATABASE & AUTH) ---
if 'users_db' not in st.session_state:
    st.session_state.users_db = pd.DataFrame([
        {
            "Username": "admin", "Password": "123", "Role": "Admin", 
            "Status": "Paid", "Pic": None, "Name": "Admin User", 
            "Mobile": "0000000000", "Email": "admin@example.com"
        }
    ])

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.current_user = None
    st.session_state.user_role = None
    st.session_state.user_status = None

# --- 3. THE RECTIFIED STYLE OVERRIDE ---
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
        
        .stApp { background-color: #0056D2; }

        /* --- NAVBAR STYLING --- */
        .stTabs [data-baseweb="tab-list"] {
            gap: 15px;
            justify-content: flex-end;
            background-color: rgba(255, 255, 255, 0.05);
            padding: 10px 20px;
            border-radius: 12px;
            margin-bottom: 30px;
        }
        
        .stTabs [data-baseweb="tab"] {
            color: #FFFFFF !important;
            font-weight: 600 !important;
            border: none !important;
            font-size: 16px !important;
        }

        /* Active Tab (White Pill Style) */
        .stTabs [aria-selected="true"] {
            background-color: #FFFFFF !important;
            color: #0056D2 !important;
            border-radius: 50px !important;
            padding: 8px 20px !important;
        }

        /* --- UNIFIED GREEN & BLUE PILL BUTTON --- */
        div.stButton > button {
            background-color: #66E035 !important;
            color: #0056D2 !important;
            border-radius: 50px !important;
            font-weight: 700 !important;
            padding: 0.6rem 2.5rem !important;
            border: none !important;
            font-size: 16px !important;
            transition: all 0.2s ease;
            box-shadow: 0 4px 10px rgba(0,0,0,0.1);
        }
        
        div.stButton > button:hover {
            transform: scale(1.05);
            box-shadow: 0 6px 15px rgba(0,0,0,0.2);
            color: #0056D2 !important;
        }

        /* --- CONTENT CARDS --- */
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

        /* Input and Label Visibility */
        input, .stSelectbox div, [data-testid="stFileUploader"] * { color: #000000 !important; font-weight: 500 !important; }
        label { color: #FFFFFF !important; font-weight: 600 !important; }
        h1, h2, h3, p, .stMarkdown { color: #FFFFFF !important; }

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
        
        # Access Check: Paid Status or Admin Role
        if st.session_state.user_role == "Admin" or st.session_state.user_status == "Paid":
            st.markdown("### 🛠️ Converter Tool (Full Access)")
            col1, col2 = st.columns(2, gap="large")
            with col1:
                with st.container(border=True):
                    st.markdown("#### 🛠️ 1. Settings & Mapping")
                    up_html = st.file_uploader("Upload Tally Master (master.html)", type=['html'])
                    ledgers = get_ledger_names(up_html) if up_html else ["Cash", "Bank"]
                    st.selectbox("Select Bank Ledger", ledgers)
                    st.selectbox("Select Default Party", ledgers)
            with col2:
                with st.container(border=True):
                    st.markdown("#### 📂 2. Upload & Convert")
                    st.selectbox("Select Bank Format", ["SBI", "HDFC", "ICICI", "Other"])
                    st.file_uploader("Drop your Bank Statement here", type=['pdf', 'xlsx'])
                    if st.button("🚀 Process & Generate XML"):
                        st.success("✅ Conversion Process Started!")
        else:
            st.warning("⚠️ Trial Mode: Please contact Admin to upgrade to a Paid account to unlock the tool.")
    else:
        st.markdown('<h1>Perfecting the Science of Data Extraction</h1>', unsafe_allow_html=True)
        st.info("👋 Welcome! Please visit the **Account** tab to Sign In.")

with tabs[1]: # SOLUTIONS
    st.markdown("## 🚀 Our Solutions")
    st.markdown("""
        <div class="content-card">
            <h4>Automated Bank Parsing</h4>
            <p>Convert SBI, HDFC, ICICI, and more into Tally XML formats with 100% precision.</p>
        </div>
        <div class="content-card">
            <h4>Master Integration</h4>
            <p>Sync your Tally ledgers instantly to ensure zero mapping errors.</p>
        </div>
    """, unsafe_allow_html=True)

with tabs[2]: # PRICING
    st.markdown("## 💰 Pricing Plans")
    p1, p2 = st.columns(2)
    with p1:
        st.markdown('<div class="content-card" style="border-top-color:#CBD5E1;"><h4>Trial Plan</h4><ul><li>Unlimited Previews</li><li>No XML Export</li></ul><b>Price: Free</b></div>', unsafe_allow_html=True)
        st.button("Start Free", key="start_trial")
    with p2:
        st.markdown('<div class="content-card"><h4>Professional Plan</h4><ul><li>Full XML Export</li><li>Priority Support</li></ul><b>Contact Admin for Access</b></div>', unsafe_allow_html=True)
        st.button("Upgrade Now", key="start_pro")

with tabs[3]: # ACCOUNT (INTEGRATED)
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
            r_name = st.text_input("Full Name *")
            r_mob = st.text_input("Mobile Number *")
            r_email = st.text_input("Email ID *")
            r_user = st.text_input("Username *")
            r_pass = st.text_input("Password *", type="password")
            
            if st.button("Create Account"):
                if all([r_name, r_mob, r_email, r_user, r_pass]):
                    new_user = {
                        "Username": r_user, "Password": r_pass, "Role": "Trial", 
                        "Status": "Free", "Pic": None, "Name": r_name, 
                        "Mobile": r_mob, "Email": r_email
                    }
                    st.session_state.users_db = pd.concat([st.session_state.users_db, pd.DataFrame([new_user])], ignore_index=True)
                    st.success("✅ Registration Successful! Please switch to Login.")
                else: st.error("Please fill in all required (*) fields.")
    else:
        # PROFILE VIEW
        idx = st.session_state.users_db[st.session_state.users_db['Username'] == st.session_state.current_user].index[0]
        data = st.session_state.users_db.iloc[idx]
        
        c1, c2 = st.columns([1, 2])
        with c1:
            if data['Pic']: st.image(data['Pic'], width=200)
            else: st.info("No photo set")
            up_pic = st.file_uploader("Update Profile Photo", type=['jpg', 'png', 'jpeg'])
            if up_pic:
                st.session_state.users_db.at[idx, 'Pic'] = up_pic
                st.rerun()
        with c2:
            st.markdown(f"### {data['Name']}")
            s_clr = "#66E035" if data['Status'] == "Paid" else "#FF4B4B"
            st.markdown(f"**Subscription:** <span style='color:{s_clr}; font-weight:bold;'>{data['Status']} User</span>", unsafe_allow_html=True)
            st.write(f"**Email:** {data['Email']}")
            if st.button("Sign Out"):
                st.session_state.logged_in = False
                st.rerun()

# --- 6. FOOTER ---
st.markdown('<div class="footer"><p>Sponsored By <b>Uday Mondal</b> | Powered & Created by <b>Debasish Biswas</b></p></div>', unsafe_allow_html=True)
