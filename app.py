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

# --- 2. THE ULTIMATE PROFESSIONAL CSS ---
st.markdown("""
    <style>
        /* Global Reset */
        .stApp { background-color: #FFFFFF; }
        header, .stDeployButton, footer { visibility: hidden !important; display: none !important; }

        /* 🟢 CLEAN HEADER BAR (Centered Text) */
        .nav-bar {
            position: fixed; top: 0; left: 0; width: 100%; height: 60px;
            background-color: #0F172A; display: flex; align-items: center;
            justify-content: center; z-index: 1000001;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .nav-logo-text { color: white; font-weight: 800; font-size: 22px; letter-spacing: 1px; }
        
        /* HAMBURGER ICON STYLING */
        [data-testid="stSidebarCollapsedControl"] {
            background-color: transparent !important;
            top: 5px !important; left: 10px !important;
            z-index: 1000002 !important;
        }
        [data-testid="stSidebarCollapsedControl"] svg { fill: white !important; width: 32px !important; height: 32px !important; }

        /* 🔵 HERO SECTION (Dark Blue Gradient) */
        .hero-section {
            background: linear-gradient(180deg, #0F172A 0%, #1E40AF 100%);
            padding: 100px 20px 80px 20px; text-align: center; color: white;
            margin: -6rem -4rem 0 -4rem;
        }
        .hero-section h1 { font-size: 2.8rem; font-weight: 800; margin-bottom: 15px; line-height: 1.2; }
        .hero-section p { font-size: 1.1rem; opacity: 0.85; max-width: 600px; margin: 0 auto; }

        /* ⚪ THE TOOL CONTAINER (Floating Card) */
        .tool-card {
            max-width: 1000px; margin: -50px auto 40px auto;
            background: white; padding: 40px; border-radius: 12px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.12); border: 1px solid #F1F5F9;
        }

        /* SIDEBAR STYLING */
        [data-testid="stSidebar"] { background-color: #0F172A !important; border-right: 3px solid #10B981 !important; }
        [data-testid="stSidebar"] * { color: white !important; }
        
        /* Modern Section Headers */
        .section-title { 
            color: #1E293B; font-size: 20px; font-weight: 700; 
            margin-bottom: 25px; border-bottom: 2px solid #10B981; 
            display: inline-block; padding-bottom: 5px;
        }
    </style>
""", unsafe_allow_html=True)

# --- 3. TOP NAVIGATION ---
st.markdown("""
    <div class="nav-bar">
        <div class="nav-logo-text">ACCOUNTING EXPERT</div>
    </div>
    """, unsafe_allow_html=True)

# --- 4. SIDEBAR ---
with st.sidebar:
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.image("https://www.w3schools.com/howto/img_avatar.png", width=70) # Replace with your logo
    st.markdown("### Navigation")
    st.divider()
    st.button("🏠 Homepage")
    st.button("⚙️ Tool Settings")
    st.button("👤 My Account")
    st.divider()
    st.write("Professional Tally Solutions")

# --- 5. THE HERO SECTION ---
st.markdown("""
    <div class="hero-section">
        <img src="https://www.w3schools.com/howto/img_avatar.png" style="width: 90px; margin-bottom: 25px;">
        <h1>Learn Accounting for Free</h1>
        <p>Professional Excel to Tally XML conversion tool. Perfect for Bookkeepers, Accountants, and Small Businesses.</p>
    </div>
    """, unsafe_allow_html=True)

# --- 6. THE FLOATING TOOL CARD ---
st.markdown('<div class="tool-card">', unsafe_allow_html=True)

col1, col2 = st.columns(2, gap="large")

with col1:
    st.markdown('<div class="section-title">🛠️ 1. Settings</div>', unsafe_allow_html=True)
    st.file_uploader("Upload Tally Master (HTML)", type=['html'], help="Upload your master file to sync ledgers.")
    st.selectbox("Bank Ledger", ["Suspense A/c", "HDFC Bank", "SBI Bank", "ICICI Bank"])

with col2:
    st.markdown('<div class="section-title">📂 2. Conversion</div>', unsafe_allow_html=True)
    st.file_uploader("Upload Bank Statement", type=['pdf', 'xlsx'])
    st.selectbox("Default Party", ["Suspense A/c", "Cash", "Sales"])

st.markdown("<br>", unsafe_allow_html=True)
if st.button("🚀 GENERATE XML FILE", use_container_width=True):
    st.balloons()
    st.success("Conversion Complete! Use the button below to save your file.")
    st.download_button("⬇️ DOWNLOAD TALLY XML", "Content", "tally_import.xml", use_container_width=True)

st.markdown('</div>', unsafe_allow_html=True)

# --- 7. AUTHOR SECTION (Matching AccountingCoach) ---
st.markdown("<br><br>", unsafe_allow_html=True)
a_col1, a_col2 = st.columns([1, 2.5])

with a_col1:
    st.image("https://www.w3schools.com/howto/img_avatar.png", width=140) # Your photo

with a_col2:
    st.markdown("### About the Developer")
    st.write("This tool was developed by **Debasish Biswas**, based in Berhampore, West Bengal. With a focus on accounting automation, this site helps professionals save hours of manual data entry by converting statements directly into Tally Prime format.")
    st.markdown("**Contact:** +91 9002043666 | **Website:** tallytools.in")

st.markdown("<br><hr><center>© 2026 Accounting Expert | Powered by TallyTools.in</center>", unsafe_allow_html=True)
