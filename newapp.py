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
        }
    ])

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.current_user = None
    st.session_state.user_role = None
    st.session_state.user_status = None

# --- 3. CUSTOM CSS (FIXING TEXT COLORS TO WHITE) ---
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
        .stApp { background-color: #0056D2; }

        /* FORCE ALL TEXTS ON BLUE BACKGROUND TO WHITE */
        h1, h2, h3, h4, h5, h6, p, span, label, .stMarkdown, [data-testid="stMarkdownContainer"] p {
            color: #FFFFFF !important;
        }

        /* NAVIGATION TABS */
        .stTabs [data-baseweb="tab-list"] {
            gap: 15px; justify-content: flex-end;
            background-color: rgba(255, 255, 255, 0.05);
            padding: 10px 20px; border-radius: 12px; margin-bottom: 30px;
        }
        .stTabs [data-baseweb="tab"] { color: #FFFFFF !important; font-weight: 600 !important; font-size: 16px !important; }
        .stTabs [aria-selected="true"] {
            background-color: #FFFFFF !important; color: #0056D2 !important; border-radius: 50px !important; padding: 8px 20px !important;
        }

        /* INPUT FIELD VISIBILITY (BLACK TEXT INSIDE WHITE BOXES) */
        input, .stSelectbox div, [data-testid="stFileUploader"] * { 
            color: #000000 !important; 
            font-weight: 500 !important; 
        }
        
        /* PILL BUTTON DESIGN */
        div.stButton > button {
            background-color: #66E035 !important; color: #0056D2 !important;
            border-radius: 50px !important; font-weight: 700 !important;
            padding: 0.6rem 2.5rem !important; border: none !important; font-size: 16px !important;
            box-shadow: 0 4px 10px rgba(0,0,0,0.1);
        }
        div.stButton > button:hover { transform: scale(1.05); color: #0056D2 !important; }

        header {visibility: hidden;}
        .footer {
            position: fixed; left: 0; bottom: 0; width: 100%;
            background-color: #FFFFFF; text-align: center; padding: 10px; z-index: 2000;
        }
        .footer p, .footer b { color: #1E293B !important; margin: 0; }
    </style>
""", unsafe_allow_html=True)

# --- 4. NAVIGATION ---
tabs = st.tabs(["Home", "Solutions", "Pricing", "Account"])

with tabs[3]: # ACCOUNT TAB
    if not st.session_state.logged_in:
        mode = st.radio("Choose Action", ["Login", "Register"], horizontal=True)
        
        if mode == "Login":
            u_in = st.text_input("Username", key="l_user")
            p_in = st.text_input("Password", type="password", key="l_pass")
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
        
        else: # REGISTER MODE
            # We use distinct keys for every widget to prevent state conflicts
            r_name = st.text_input("Full Name *", key="reg_name")
            r_mob = st.text_input("Mobile Number *", key="reg_mob")
            r_email = st.text_input("Email ID *", key="reg_email")
            r_user = st.text_input("Username *", key="reg_user")
            r_pass = st.text_input("Password *", type="password", key="reg_pass")
            r_status = st.selectbox("Select Package", ["Free", "Paid"], key="reg_pkg")
            r_comp = st.text_input("Company Name (Optional)", key="reg_comp")
            
            if st.button("Create Account"):
                # FIX: Explicitly check only the required fields
                # We use .strip() to ensure spaces aren't counted as input
                required_data = [r_name, r_mob, r_email, r_user, r_pass]
                
                if all(val and str(val).strip() != "" for val in required_data):
                    new_user = {
                        "Username": r_user, 
                        "Password": r_pass, 
                        "Role": "Trial", 
                        "Status": r_status, 
                        "Pic": None, 
                        "Name": r_name, 
                        "Mobile": r_mob, 
                        "Email": r_email,
                        "Company": r_comp if r_comp.strip() else "N/A"
                    }
                    st.session_state.users_db = pd.concat([st.session_state.users_db, pd.DataFrame([new_user])], ignore_index=True)
                    st.success("✅ Registration Successful! Please switch to Login.")
                else:
                    # This will now only show if one of the first 5 fields is empty
                    st.error("Please fill in all required (*) fields.")

# --- 5. FOOTER ---
st.markdown('<div class="footer"><p>Sponsored By <b>Uday Mondal</b> | Powered & Created by <b>Debasish Biswas</b></p></div>', unsafe_allow_html=True)
