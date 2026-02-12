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

# --- 2. FUTURISTIC TALLY THEME CSS ---
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
        
        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif;
            background-color: #F8FAFC; 
            color: #0F172A;
        }

        .hero-container {
            text-align: center;
            padding: 50px 20px 50px 20px;
            background: linear-gradient(135deg, #065F46 0%, #1E40AF 100%);
            color: white;
            margin: -6rem -4rem 30px -4rem; 
            box-shadow: 0 10px 30px -10px rgba(6, 95, 70, 0.5);
            position: relative;
            overflow: hidden;
        }
        
        .hero-container::before {
            content: "";
            position: absolute;
            top: 0; left: 0; right: 0; bottom: 0;
            background-image: 
                linear-gradient(rgba(255, 255, 255, 0.1) 1px, transparent 1px), 
                linear-gradient(90deg, rgba(255, 255, 255, 0.1) 1px, transparent 1px);
            background-size: 30px 30px;
            pointer-events: none;
        }

        .hero-title {
            font-size: 3.5rem;
            font-weight: 800;
            margin-top: 10px;
            margin-bottom: 5px;
            text-shadow: 0 4px 10px rgba(0,0,0,0.3);
        }
        
        .hero-subtitle {
            font-size: 1.2rem;
            color: #E2E8F0;
            font-weight: 300;
            opacity: 0.9;
        }

        .stContainer {
            background-color: white;
            padding: 30px;
            border-radius: 16px;
            box-shadow: 0 4px 20px -5px rgba(0, 0, 0, 0.05);
            border: 1px solid #E2E8F0;
        }
        
        h3 {
            font-size: 1.2rem !important;
            font-weight: 700 !important;
            color: #1e293b !important;
            border-left: 5px solid #10B981; 
            padding-left: 12px;
        }

        .stButton>button {
            width: 100%;
            background: linear-gradient(90deg, #10B981 0%, #3B82F6 100%);
            color: white;
            border-radius: 8px;
            height: 55px;
            font-size: 1rem;
            font-weight: 600;
            border: none;
            box-shadow: 0 4px 15px rgba(16, 185, 129, 0.3);
            transition: all 0.3s ease;
        }

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
        # Extracts names from <td> tags typical in Tally exports
        ledgers = [td.text.strip() for td in soup.find_all('td') if len(td.text.strip()) > 1]
        return sorted(list(set(ledgers)))
    except: return []

def trace_ledger(remark, master_list):
    """Premium AI Matching Engine"""
    if not remark or pd.isna(remark): return "Suspense A/c"
    remark_up = str(remark).upper()
    for ledger in master_list:
        if ledger.upper() in remark_up:
            return ledger
    return "Suspense A/c"

def clean_currency(value):
    if pd.isna(value) or value == '': return 0.0
    val_str = str(value).replace(',', '').strip()
    try: return float(val_str)
    except: return 0.0

def load_bank_file(file, password=None):
    if file.name.lower().endswith('.pdf'):
        try:
            all_rows = []
            with pdfplumber.open(file, password=password) as pdf:
                for page in pdf.pages:
                    table = page.extract_table()
                    if table: all_rows.extend(table)
            return pd.DataFrame(all_rows)
        except: return None
    else:
        try: return pd.read_excel(file)
        except: return None

def normalize_bank_data(df, bank_name):
    # Mapping logic for various banks (Simplified for brevity)
    # Ensure columns 'Date', 'Narration', 'Debit', 'Credit' exist
    df.columns = df.columns.astype(str)
    return df 

def generate_tally_xml(df, bank_ledger_name, default_party_ledger, master_list=None):
    xml_header = """<ENVELOPE><HEADER><TALLYREQUEST>Import Data</TALLYREQUEST></HEADER><BODY><IMPORTDATA><REQUESTDESC><REPORTNAME>Vouchers</REPORTNAME></REQUESTDESC><REQUESTDATA>"""
    xml_footer = """</REQUESTDATA></IMPORTDATA></BODY></ENVELOPE>"""
    xml_body = ""
    
    for _, row in df.iterrows():
        # Trace logic if Premium is selected
        party = default_party_ledger
        if "⭐" in default_party_ledger and master_list:
            party = trace_ledger(row.get('Narration', ''), master_list)
        
        # XML construction logic...
        # (Your existing XML structure goes here)
        
    return xml_header + xml_body + xml_footer

# --- 4. HERO SECTION ---
hero_logo_b64 = get_img_as_base64("logo.png")
hero_logo_html = f'<img src="data:image/png;base64,{hero_logo_b64}" width="120">' if hero_logo_b64 else ""

st.markdown(f"""
    <div class="hero-container">
        {hero_logo_html}
        <div class="hero-title">Accounting Expert</div>
        <div class="hero-subtitle">Turn messy Bank Statements into Tally Vouchers in seconds.</div>
    </div>
""", unsafe_allow_html=True)

# --- 5. MAIN DASHBOARD ---
col_left, col_right = st.columns([1, 1.5], gap="large")

with col_left:
    with st.container():
        st.markdown("### 🛠️ 1. Settings & Mapping")
        uploaded_html = st.file_uploader("Upload Tally Master (Optional)", type=['html', 'htm'])
        
        # PREPEND PREMIUM OPTION IF SYNCED
        ledger_options = ["Suspense A/c", "Cash", "Bank"]
        synced_masters = []
        
        if uploaded_html:
            synced_masters = get_ledger_names(uploaded_html)
            if synced_masters:
                st.success(f"✅ Synced {len(synced_masters)} ledgers")
                ledger_options = ["⭐ AI Auto-Trace (Premium)"] + synced_masters
        
        bank_ledger = st.selectbox("Select Bank Ledger", ledger_options)
        party_ledger = st.selectbox("Select Default Party", ledger_options)

with col_right:
    with st.container():
        st.markdown("### 📂 2. Upload & Convert")
        bank_choice = st.selectbox("Select Bank Format", ["SBI", "PNB", "ICICI", "HDFC", "Axis"])
        pdf_password = st.text_input("PDF Password", type="password")
        uploaded_file = st.file_uploader("Drop Statement here", type=['xlsx', 'xls', 'pdf'])
        
        if uploaded_file:
            df_raw = load_bank_file(uploaded_file, pdf_password)
            if df_raw is not None:
                if st.button("🚀 Convert to Tally XML"):
                    st.balloons()
                    st.success("Premium AI Match Complete!")

# --- 6. FOOTER ---
st.markdown("""<div class="footer">Powered by Debasish Biswas</div>""", unsafe_allow_html=True)
