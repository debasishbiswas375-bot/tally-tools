import streamlit as st
import pandas as pd
import re

# --- 1. PAGE CONFIG ---
st.set_page_config(
    page_title="Accounting Expert", 
    page_icon="logo.png",
    layout="wide",
    initial_sidebar_state="collapsed" 
)

# --- 2. THE ACCOUNTING COACH "CLONE" ENGINE ---
st.markdown("""
    <style>
        /* 1. Navbar: Dark Teal/Blue thin strip */
        header, .stDeployButton, footer { visibility: hidden !important; display: none !important; }
        
        .custom-nav {
            background-color: #004b63;
            height: 60px;
            width: 100%;
            position: fixed;
            top: 0;
            left: 0;
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0 15px;
            z-index: 999999;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
        }
        
        /* Centered Logo in Nav */
        .nav-logo {
            color: white;
            font-family: 'Serif', 'Times New Roman';
            font-size: 24px;
            font-weight: bold;
            text-align: center;
            flex-grow: 1;
        }

        /* 2. Hamburger override for left-side placement */
        [data-testid="stSidebarCollapsedControl"] {
            background-color: transparent !important;
            top: 5px !important;
            left: 5px !important;
            z-index: 1000000 !important;
        }
        [data-testid="stSidebarCollapsedControl"] svg { fill: white !important; width: 35px !important; }

        /* 3. Hero Section: Direct Clone of the Blue/Teal Gradient */
        .hero-section {
            background: radial-gradient(circle at center, #11819d 0%, #004b63 100%);
            color: white;
            text-align: center;
            padding: 100px 20px 80px 20px;
            margin: -6rem -4rem 0 -4rem;
        }
        .hero-section h1 {
            font-size: 3.5rem;
            font-weight: 700;
            margin-bottom: 20px;
            font-family: 'Serif', 'Times New Roman';
        }
        .hero-section p {
            font-size: 1.3rem;
            max-width: 700px;
            margin: 0 auto 30px auto;
            line-height: 1.5;
        }

        /* 4. White Section Below Hero */
        .white-section {
            background-color: white;
            padding: 40px 20px;
            margin: 0 -4rem;
            text-align: center;
        }

        /* 5. Tool Container: Styled like their 'Choose a Topic' boxes */
        .tool-box {
            background-color: #f8fbfc;
            border: 1px solid #e1e8ed;
            border-radius: 4px;
            padding: 25px;
            margin-top: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        }
        
        /* Main Button: White background with blue border like 'Course Outline' */
        .stButton>button {
            background-color: white !important;
            color: #004b63 !important;
            border: 2px solid #004b63 !important;
            font-weight: bold !important;
            border-radius: 0 !important;
            height: 50px !important;
            text-transform: uppercase;
        }
    </style>
""", unsafe_allow_html=True)

# --- 3. CUSTOM NAVBAR ---
st.markdown("""
    <div class="custom-nav">
        <div style="width: 40px;"></div> <div class="nav-logo">AccountingExpert</div>
        <div style="color:white; font-size: 20px;">🔍</div>
    </div>
""", unsafe_allow_html=True)

# --- 4. HERO SECTION ---
st.markdown("""
    <div class="hero-section">
        <h1>Convert Excel to Tally for Free</h1>
        <p>Perfect for Employees, Bookkeepers, Students, Accountants, and Small Businesses.</p>
    </div>
""", unsafe_allow_html=True)

# --- 5. TRUST LOGO BAR ---
st.markdown("""
    <div class="white-section">
        <p style="color: #666; font-size: 14px; margin-bottom: 20px;">TRUSTED BY PROFESSIONALS IN WEST BENGAL</p>
        <div style="display: flex; justify-content: center; gap: 30px; opacity: 0.5; flex-wrap: wrap;">
             <span style="font-weight: bold; font-size: 20px;">TALLY</span>
             <span style="font-weight: bold; font-size: 20px;">MSME</span>
             <span style="font-weight: bold; font-size: 20px;">GSTN</span>
             <span style="font-weight: bold; font-size: 20px;">ICAI</span>
        </div>
    </div>
""", unsafe_allow_html=True)

# --- 6. THE CONVERSION TOOL (White background section) ---
st.markdown("### Choose Your Action Below")
col1, col2 = st.columns(2, gap="large")

with col1:
    st.markdown('<div class="tool-box">', unsafe_allow_html=True)
    st.markdown("#### 🛠️ 1. Settings")
    st.file_uploader("Upload Tally Master (HTML)", type=['html'])
    st.selectbox("Select Bank Ledger", ["Suspense A/c", "HDFC Bank", "SBI"])
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="tool-box">', unsafe_allow_html=True)
    st.markdown("#### 📂 2. Conversion")
    st.file_uploader("Upload Statement", type=['pdf', 'xlsx'])
    st.selectbox("Default Party Name", ["Suspense A/c", "Cash"])
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
if st.button("🚀 GENERATE XML FILE", use_container_width=True):
    st.success("File Ready for Download")

# --- 7. AUTHOR SECTION (Same as AccountingCoach) ---
st.markdown("<hr>", unsafe_allow_html=True)
c_pic, c_text = st.columns([1, 3])
with c_pic:
    st.image("https://www.w3schools.com/howto/img_avatar.png", width=150)
with c_text:
    st.markdown("### About the Author")
    st.write("Debasish Biswas has been helping accountants automate their workflow for years. He is the sole developer of **tallytools.in**, designed to make manual entry a thing of the past.")
    st.write("📍 Berhampore, WB | 📞 +91 9002043666")

st.markdown("<br><br><center>© 2026 Accounting Expert | tallytools.in</center>", unsafe_allow_html=True)
