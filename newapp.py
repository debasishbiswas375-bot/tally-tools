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

# --- 3. CUSTOM CSS ---
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
        .stApp { background-color: #0056D2; }

        /* LOGO PLACEMENT IN TOP LEFT (Green Area) */
        [data-testid="stHeader"]::before {
            content: "";
            background-image: url("https://your-image-host.com/logo.png"); /* Replace with your actual URL */
            background-size: contain;
            background-repeat: no-repeat;
            position: absolute;
            left: 50px;
            top: 20px;
            width: 150px;
            height: 60px;
            z-index: 9999;
        }

        /* FORCE TEXTS TO WHITE */
        h1, h2, h3, h4, h5, h6, p, span, label, .stMarkdown, [data-testid="stMarkdownContainer"] p {
            color: #FFFFFF !important;
        }

        /* NAVBAR STYLING */
        .stTabs [data-baseweb="tab-list"] {
            gap: 15px; justify-content: flex-end;
            background-color: rgba(255, 255, 255, 0.05);
            padding: 10px 20px; border-radius: 12px; margin-bottom: 30px;
        }
        .stTabs [data-baseweb="tab"] { color: #FFFFFF !important; font-weight: 600 !important; font-size: 16px !important; }
        .stTabs [aria-selected="true"] {
            background-color: #FFFFFF !important; color: #0056D2 !important; border-radius: 50px !important; padding: 8px 20px !important;
        }

        /* INPUT FIELD VISIBILITY */
        input, .stSelectbox div, [data-testid="stFileUploader"] * { color: #000000 !important; font-weight: 500 !important; }
        
        /* PILL BUTTON DESIGN */
        div.stButton > button {
            background-color: #66E035 !important; color: #0056D2 !important;
            border-radius: 50px !important; font-weight: 700 !important;
            padding: 0.6rem 2.5rem !important; border: none !important; font-size: 16px !important;
        }

        header {visibility: hidden;}
        
        /* RECTIFIED FOOTER WITH LOGO 1.PNG */
        .footer {
            position: fixed; left: 0; bottom: 0; width: 100%;
            background-color: #FFFFFF; text-align: center; padding: 10px; z-index: 2000;
            display: flex; align-items: center; justify-content: center; gap: 8px;
        }
        .footer p, .footer b { color: #1E293B !important; margin: 0; }
        .footer img { height: 20px; vertical-align: middle; }
    </style>
""", unsafe_allow_html=True)

# --- 4. NAVIGATION ---
tabs = st.tabs(["Home", "Solutions", "Pricing", "Account"])

# --- 5. ACCOUNT LOGIC (Fixed Registration) ---
with tabs[3]:
    if not st.session_state.logged_in:
        mode = st.radio("Choose Action", ["Login", "Register"], horizontal=True)
        if mode == "Register":
            r_name = st.text_input("Full Name *", key="reg_name")
            r_mob = st.text_input("Mobile Number *", key="reg_mob")
            r_email = st.text_input("Email ID *", key="reg_email")
            r_user = st.text_input("Username *", key="reg_user")
            r_pass = st.text_input("Password *", type="password", key="reg_pass")
            r_status = st.selectbox("Select Package", ["Free", "Paid"], key="reg_pkg")
            r_comp = st.text_input("Company Name (Optional)", key="reg_comp")
            
            if st.button("Create Account"):
                required = [r_name, r_mob, r_email, r_user, r_pass]
                if all(v.strip() != "" for v in required):
                    new_user = {
                        "Username": r_user, "Password": r_pass, "Role": "Trial", "Status": r_status,
                        "Pic": None, "Name": r_name, "Mobile": r_mob, "Email": r_email,
                        "Company": r_comp if r_comp.strip() else "N/A"
                    }
                    st.session_state.users_db = pd.concat([st.session_state.users_db, pd.DataFrame([new_user])], ignore_index=True)
                    st.success("✅ Registration Successful!")
                else:
                    st.error("Please fill in all required (*) fields.")
        else:
            # Login logic here...
            pass

# --- 6. FOOTER WITH LOGO 1.PNG ---
st.markdown(f"""
    <div class="footer">
        <p>Sponsored By <img src="https://your-image-host.com/logo1.png"> <b>Uday Mondal</b> | Powered & Created by <b>Debasish Biswas</b></p>
    </div>
""", unsafe_allow_html=True)
