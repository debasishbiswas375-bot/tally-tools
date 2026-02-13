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

# --- 2. THE PROFESSIONAL DESIGN ENGINE (CSS) ---
st.markdown("""
    <style>
        /* Global Background */
        .stApp { background-color: #FFFFFF; }

        /* Hide Streamlit default headers & footers */
        header, .stDeployButton, footer { visibility: hidden !important; display: none !important; }

        /* 🟢 NAVIGATION BAR (Clean & Pro) */
        .nav-bar {
            position: fixed; top: 0; left: 0; width: 100%; height: 65px;
            background-color: #0F172A; display: flex; align-items: center;
            justify-content: space-between; padding: 0 20px; z-index: 1000001;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .nav-logo-text { color: white; font-weight: 800; font-size: 20px; letter-spacing: 1px; }

        /* HAMBURGER MENU OVERRIDE */
        [data-testid="stSidebarCollapsedControl"] {
            background-color: transparent !important;
            top: 10px !important; left: 10px !important;
            z-index: 1000002 !important;
        }
        [data-testid="stSidebarCollapsedControl"] svg { fill: white !important; width: 30px !important; height: 30px !important; }

        /* 🔵 HERO SECTION (Large & Bold) */
        .hero-section {
            background: linear-gradient(180deg, #0F172A 0%, #1E40AF 100%);
            padding: 100px 20px 60px 20px; text-align: center; color: white;
            margin: -6rem -4rem 0 -4rem;
        }
        .hero-section h1 { font-size: 3rem; font-weight: 800; margin-bottom: 10px; }
        .hero-section p { font-size: 1.2rem; opacity: 0.9; }

        /* ⚪ TOOL SECTION (Clean White Background) */
        .tool-container {
            max-width: 900px; margin: -40px auto 40px auto;
            background: white; padding: 30px; border-radius: 15px;
            box-shadow: 0 15px 35px rgba(0,0,0,0.1); border: 1px solid #E2E8F0;
        }

        /* SIDEBAR STYLING */
        [data-testid="stSidebar"] {
            background-color: #0F172A !important;
            border-right: 3px solid #10B981 !important;
        }
        [data-testid="stSidebar"] * { color: white !important; }
        
        /* Heading Colors */
        .section-header { color: #1E293B; font-weight: 700; border-left: 5px solid #10B981; padding-left: 15px; margin-bottom: 20px; }
    </style>
""", unsafe_allow_html=True)

# --- 3. CUSTOM TOP NAVIGATION ---
st.markdown("""
    <div class="nav-bar">
        <div style="width: 40px;"></div> <div class="nav-logo-text">ACCOUNTING EXPERT</div>
        <img src="https://www.w3schools.com/howto/img_avatar.png" style="width: 38px; border-radius: 50%; border: 2px solid #10B981;">
    </div>
    """, unsafe_allow_html=True)

# --- 4. SIDEBAR ---
with st.sidebar:
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.image("https://www.w3schools.com/howto/img_avatar.png", width=80) 
    st.markdown('<h3 style="color: #10B981;">Menu</h3>', unsafe_allow_html=True)
    st.divider()
    st.button("🏠 Home", use_container_width=True)
    st.button("📊 Dashboard", use_container_width=True)
    st.button("📞 Contact Support", use_container_width=True)

# --- 5. THE PROFESSIONAL HERO ---
st.markdown("""
    <div class="hero-section">
        <img src="https://www.w3schools.com/howto/img_avatar.png" style="width: 100px; margin-bottom: 20px;">
        <h1>Learn Accounting for Free</h1>
        <p>Perfect for Employees, Bookkeepers, and Small Businesses.</p>
    </div>
    """, unsafe_allow_html=True)

# --- 6. THE CONVERSION TOOL (White Box Section) ---
# Wrapping the Streamlit columns in a container div for the shadow effect
st.markdown('<div class="tool-container">', unsafe_allow_html=True)

st.markdown('<div class="section-header">🛠️ Conversion Settings</div>', unsafe_allow_html=True)

t_col1, t_col2 = st.columns(2, gap="large")

with t_col1:
    st.file_uploader("Upload Tally Master (HTML)", type=['html'])
    st.selectbox("Select Bank Ledger", ["Suspense A/c", "HDFC Bank", "SBI Bank"])

with t_col2:
    st.file_uploader("Upload Bank Statement", type=['pdf', 'xlsx'])
    st.selectbox("Default Party Name", ["Suspense A/c", "Cash"])

st.write("---")
if st.button("🚀 GENERATE TALLY XML", use_container_width=True):
    st.balloons()
    st.success("Conversion Ready! Download below.")

st.markdown('</div>', unsafe_allow_html=True)

# --- 7. ABOUT SECTION (Like AccountingCoach) ---
st.markdown("<br>", unsafe_allow_html=True)
col_a, col_b = st.columns([1, 2])
with col_a:
    st.image("https://www.w3schools.com/howto/img_avatar.png", width=150)
with col_b:
    st.markdown("### About the Developer")
    st.write("Developed by **Debasish Biswas**, providing professional Tally automation tools for accountants in West Bengal. Our mission is to make data entry 10x faster.")
    st.write("📍 Berhampore, West Bengal | 📞 +91 9002043666")

st.markdown("<br><hr><center>© 2026 tallytools.in | All Rights Reserved</center>", unsafe_allow_html=True)
