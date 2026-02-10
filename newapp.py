import streamlit as st
import pandas as pd
from PIL import Image
from bs4 import BeautifulSoup
import pdfplumber
import io
import base64

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Accounting Expert | AI Bank to Tally",
    page_icon="logo.png",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 2. CAELUM.AI EXACT CLONE CSS ---
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
        
        /* Global Settings */
        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif;
            background-color: #F8FAFC; 
            color: #0F172A;
            overflow-x: hidden;
        }

        /* --- NAVIGATION BAR (Mock) --- */
        .nav-container {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 20px 50px;
            background-color: #0044CC; /* Caelum Blue */
            color: white;
            font-size: 0.9rem;
            font-weight: 500;
            margin: -6rem -4rem 0 -4rem; /* Stretch to top */
        }
        .nav-logo {
            font-size: 1.5rem;
            font-weight: 800;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .nav-links {
            display: flex;
            gap: 30px;
            align-items: center;
        }
        .nav-link { color: white; text-decoration: none; opacity: 0.9; cursor: pointer; }
        .nav-link:hover { opacity: 1; text-decoration: underline; }
        
        .nav-btn-login {
            border: 1px solid white;
            padding: 8px 20px;
            border-radius: 50px;
            background: transparent;
            color: white;
            cursor: pointer;
        }
        .nav-btn-trial {
            background-color: #4ADE80; /* Bright Green */
            color: #0044CC;
            padding: 8px 20px;
            border-radius: 50px;
            border: none;
            font-weight: 700;
            cursor: pointer;
        }

        /* --- HERO SECTION --- */
        .hero-section {
            background-color: #0044CC; /* The Main Blue */
            color: white;
            padding: 60px 80px 100px 80px;
            margin: 0 -4rem 30px -4rem;
            display: flex;
            align-items: center;
            justify-content: space-between;
            position: relative;
            overflow: hidden;
        }
        
        /* Background decorative circles (Subtle) */
        .hero-section::before {
            content: '';
            position: absolute;
            width: 400px;
            height: 400px;
            background: rgba(255, 255, 255, 0.03);
            border-radius: 50%;
            top: -100px;
            right: -50px;
        }

        .hero-content {
            max-width: 55%;
            z-index: 2;
        }
        
        .hero-title {
            font-size: 3.5rem;
            font-weight: 800;
            line-height: 1.1;
            margin-bottom: 20px;
        }
        
        .hero-subtitle {
            font-size: 1.1rem;
            opacity: 0.9;
            line-height: 1.6;
            margin-bottom: 30px;
            max-width: 90%;
        }

        .hero-cta {
            background-color: #4ADE80; /* The Green Button */
            color: #0044CC;
            padding: 15px 35px;
            border-radius: 50px;
            font-weight: 700;
            border: none;
            font-size: 1rem;
            display: inline-block;
            box-shadow: 0 4px 15px rgba(74, 222, 128, 0.3);
        }

        .hero-image-container {
            width: 40%;
            display: flex;
            justify-content: center;
            z-index: 2;
        }
        
        .hero-image-container img {
            max-width: 100%;
            filter: drop-shadow(0 10px 20px rgba(0,0,0,0.2));
            animation: float 6s ease-in-out infinite;
        }

        @keyframes float {
            0% { transform: translateY(0px); }
            50% { transform: translateY(-15px); }
            100% { transform: translateY(0px); }
        }

        /* --- MAIN APP CARDS --- */
        .stContainer {
            background-color: white;
            padding: 30px;
            border-radius: 12px;
            box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.05);
            border: 1px solid #E2E8F0;
        }
        
        h3 {
            color: #0F172A !important;
            font-weight: 700 !important;
        }

        /* Streamlit Buttons to match the Green Theme */
        .stButton>button {
            background-color: #0044CC; /* Blue */
            color: white;
            border-radius: 8px;
            height: 50px;
            font-weight: 600;
            border: none;
        }
        .stButton>button:hover {
            background-color: #003399;
        }
        
        /* The GENERATE Button specifically */
        div[data-testid="stButton"] button {
             background-color: #4ADE80 !important; /* Green */
             color: #0044CC !important;
             font-weight: 800 !important;
        }

        /* Footer */
        .footer {
            margin-top: 60px;
            padding: 40px;
            text-align: center;
            color: #64748B;
            font-size: 0.9rem;
            border-top: 1px solid #E2E8F0;
            background-color: white;
            margin-bottom: -60px;
        }
        .brand-link { color: #0044CC; font-weight: 700; text-decoration: none; }
        
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- 3. HELPER FUNCTIONS ---

def get_img_as_base64(file):
    try:
        with open(file, "rb") as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except: return None

def get_ledger_names(html_file):
    try:
        soup = BeautifulSoup(html_file, 'html.parser')
        ledgers = []
        rows = soup.find_all('tr')
        for row in rows:
            cols = row.find_all('td')
            if cols:
                text = cols[0].get_text(strip=True)
                if text: ledgers.append(text)
        if not ledgers:
            all_text = soup.get_text(separator='\n')
            lines = [line.strip() for line in all_text.split('\n') if line.strip()]
            ledgers = sorted(list(set(lines)))
        return sorted(ledgers)
    except: return []

def clean_currency(value):
    if pd.isna(value) or value == '': return 0.0
    val_str = str(value).replace(',', '').strip()
    try: return float(val_str)
    except: return 0.0

# PDF Extraction
def extract_data_from_pdf(file, password=None):
    all_rows = []
    try:
        with pdfplumber.open(file, password=password) as pdf:
            for page in
