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

# --- 2. SESSION STATE (USER DATABASE & AUTH) ---
if 'users_db' not in st.session_state:
    # Initial database with requested fields
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

# --- 3. CUSTOM CSS (FIXING CONTRAST & VISIBILITY) ---
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
        .stApp { background-color: #0056D2; }

        /* NAVIGATION TABS */
        .stTabs [data-baseweb="tab-list"] { gap: 20px; justify-content: flex-end; }
        .stTabs [data-baseweb="tab"] { color: #FFFFFF !important; font-weight: 600; }
        .stTabs [aria-selected="true"] { background-color: #FFFFFF !important; color: #0056D2 !important; border-radius: 8px 8px 0 0; }

        /* INPUT VISIBILITY (FORCING BLACK TEXT) */
        input, .stSelectbox div, [data-testid="stFileUploader"] * { color: #000000 !important; }
        label { color: #FFFFFF !important; font-weight: 600 !important; }
        h1, h2, h3, p, .stMarkdown { color: #FFFFFF !important; }

        /* PRICING CARDS - HIGH CONTRAST FIX */
        .price-card {
            background-color: #FFFFFF;
            padding: 25px;
            border-radius: 15px;
            color: #1E293B !important;
            min-height: 250px;
            border-top: 8px solid #66E035;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        }
        .price-card h4 { color: #0056D2 !important; font-weight: 800; margin-bottom: 15px; }
        .price-card ul { color: #1E293B !important; list-style-type: none; padding-left: 0; }
        .price-card li { margin-bottom: 10px; font-weight: 500; }
        .price-card b { color: #0056D2; font-size: 1.2em; }

        /* BUTTONS */
        div.stButton > button {
            background-color: #66E035 !important;
            color: #0056D2 !important;
            border-radius: 50px !important;
            font-weight: 700 !important;
            border: none !important;
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
                    st.selectbox("Select Bank Format", ["SBI", "HDFC", "ICICI", "Other"])
                    up_html = st.file_uploader("Upload Tally Master (master.html)", type=['html'])
                    ledgers = get_ledger_names(up_html) if up_html else ["Cash", "Bank"]
                    st.selectbox("Select Bank Ledger", ledgers)
            with col2:
                with st.container(border=True):
                    st.markdown("#### 2. Process")
                    st.file_uploader("Drop Bank Statement here", type=['pdf', 'xlsx'])
                    if st.button("🚀 Process & Generate XML"):
                        st.success("✅ Conversion Process Started!")
        else:
            st.warning("⚠️ Trial Mode: Please contact Admin to upgrade to a Paid account for XML Export.")
    else:
        st.markdown('<h1>Perfecting the Science of Data Extraction</h1>', unsafe_allow_html=True)
        st.info("👋 Welcome! Please visit the **Account** tab to Sign In or Register.")

with tabs[1]: # SOLUTIONS
    st.markdown("## 🚀 Our Solutions")
    st.markdown("""
    * **Bank to Tally XML:** Convert any PDF/Excel statement into Tally-ready format.
    * **Auto-Ledger Mapping:** Fetch ledgers directly from your Tally HTML masters.
    * **High Security:** Processing happens locally in your session.
    """)

with tabs[2]: # PRICING
    st.markdown("## 💰 Plans & Pricing")
    p1, p2 = st.columns(2)
    with p1:
        st.markdown("""
            <div class="price-card" style="border-top-color: #CBD5E1;">
                <h4>Trial Plan</h4>
                <ul>
                    <li>✅ Unlimited Previews</li>
                    <li>❌ Restricted XML Export</li>
                    <li>✅ Standard Support</li>
                </ul>
                <b>Price: Free</b>
            </div>
        """, unsafe_allow_html=True)
    with p2:
        st.markdown("""
            <div class="price-card">
                <h4>Professional Plan</h4>
                <ul>
                    <li>✅ Full XML Export</li>
                    <li>✅ All Bank Formats Supported</li>
                    <li>✅ Priority Admin Support</li>
                </ul>
                <b>Contact Admin for Pricing</b>
            </div>
        """, unsafe_allow_html=True)

with tabs[3]: # ACCOUNT (INTEGRATED LOGIN, REGISTER & PROFILE)
    if not st.session_state.logged_in:
        mode = st.radio("Select Action", ["Login", "Register"], horizontal=True)
        
        if mode == "Login":
            u_input = st.text_input("Username", key="login_u")
            p_input = st.text_input("Password", type="password", key="login_p")
            if st.button("Sign In"):
                db = st.session_state.users_db
                match = db[(db['Username'] == u_input) & (db['Password'] == p_input)]
                if not match.empty:
                    st.session_state.logged_in = True
                    st.session_state.current_user = u_input
                    st.session_state.user_role = match.iloc[0]['Role']
                    st.rerun()
                else: st.error("Invalid Username or Password.")
        else:
            # Registration with new required fields
            r_name = st.text_input("Full Name *")
            r_mob = st.text_input("Mobile Number *")
            r_email = st.text_input("Email ID *")
            r_user = st.text_input("Choose Username *")
            r_pass = st.text_input("Choose Password *", type="password")
            r_comp = st.text_input("Company Name (Optional)")
            
            if st.button("Create Account"):
                if all([r_name, r_mob, r_email, r_user, r_pass]):
                    new_user = {
                        "Username": r_user, "Password": r_pass, "Role": "Trial", 
                        "Status": "Free", "Pic": None, "Name": r_name, 
                        "Mobile": r_mob, "Email": r_email, "Company": r_comp if r_comp else "N/A"
                    }
                    st.session_state.users_db = pd.concat([st.session_state.users_db, pd.DataFrame([new_user])], ignore_index=True)
                    st.success("✅ Registration Successful! You can now switch to Login.")
                else:
                    st.error("Please fill in all required (*) fields.")
    
    else:
        # PROFILE VIEW
        st.markdown("## 👤 Your Profile")
        idx = st.session_state.users_db[st.session_state.users_db['Username'] == st.session_state.current_user].index[0]
        data = st.session_state.users_db.iloc[idx]

        c_img, c_info = st.columns([1, 2])
        with c_img:
            if data['Pic'] is not None:
                st.image(data['Pic'], width=200)
            else:
                st.info("No profile picture.")
            
            new_photo = st.file_uploader("Update Profile Photo", type=['jpg', 'png', 'jpeg'])
            if new_photo:
                st.session_state.users_db.at[idx, 'Pic'] = new_photo
                st.rerun()

        with c_info:
            st.markdown(f"### {data['Name']}")
            status_color = "#66E035" if data['Status'] == "Paid" else "#FF4B4B"
            st.markdown(f"**Subscription Status:** <span style='color:{status_color}; font-weight:bold;'>{data['Status']} User</span>", unsafe_allow_html=True)
            st.write(f"**Username:** {data['Username']}")
            st.write(f"**Email:** {data['Email']}")
            st.write(f"**Mobile:** {data['Mobile']}")
            st.write(f"**Company:** {data['Company']}")
            
            if st.button("Sign Out"):
                st.session_state.logged_in = False
                st.rerun()

# --- 6. FOOTER ---
st.markdown("""
    <div class="footer">
        <p>Sponsored By <b>Uday Mondal</b> | Powered & Created by <b>Debasish Biswas</b></p>
    </div>
""", unsafe_allow_html=True)
