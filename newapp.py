import streamlit as st
import pandas as pd
from bs4 import BeautifulSoup
import pdfplumber
import base64
import io
from PIL import Image

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Accounting Expert",
    page_icon="logo.png",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 2. SESSION STATE (FIXED: Initializing 'Pic' column correctly) ---
if 'users_db' not in st.session_state:
    st.session_state.users_db = pd.DataFrame([
        {"Username": "admin", "Password": "123", "Role": "Admin", "Pic": None},
        {"Username": "uday", "Password": "123", "Role": "User", "Pic": None}
    ])

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.current_user = None
    st.session_state.show_settings = False

# --- 3. CUSTOM CSS ---
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
        .stApp { background-color: #0056D2; }
        .stTabs { background-color: #0056D2; position: sticky; top: 0; z-index: 1000; }
        .stTabs [data-baseweb="tab"] { color: #FFFFFF !important; font-weight: 600; }
        .stTabs [aria-selected="true"] { background-color: #FFFFFF !important; color: #0056D2 !important; border-radius: 8px; }
        h1, h2, h3, p, label, .stMarkdown { color: #FFFFFF !important; }
        .footer { position: fixed; left: 0; bottom: 0; width: 100%; background-color: #FFFFFF; text-align: center; padding: 10px; z-index: 2000; border-top: 1px solid #ddd; }
        .footer p, .footer b { color: #333 !important; margin: 0; }
        div[data-testid="stButton"] button { background-color: #66E035; color: #0056D2; border-radius: 50px; font-weight: 700; border: none; }
        header {visibility: hidden;}
        .main .block-container { padding-bottom: 120px; }
    </style>
""", unsafe_allow_html=True)

# --- 4. DATA PROCESSING LOGIC ---
def get_ledger_names(html_file):
    try:
        soup = BeautifulSoup(html_file, 'html.parser')
        ledgers = [td.get_text(strip=True) for td in soup.find_all('td') if td.get_text(strip=True)]
        if not ledgers:
            all_text = soup.get_text(separator='\n')
            ledgers = [line.strip() for line in all_text.split('\n') if line.strip()]
        return sorted(list(set(ledgers)))
    except: return []

def clean_currency(value):
    if pd.isna(value) or value == '': return 0.0
    try: return float(str(value).replace(',', '').strip())
    except: return 0.0

def load_bank_file(file, password=None):
    if file.name.lower().endswith('.pdf'):
        all_rows = []
        with pdfplumber.open(file, password=password) as pdf:
            for page in pdf.pages:
                table = page.extract_table()
                if table: all_rows.extend(table)
        df = pd.DataFrame(all_rows)
        for i, row in df.iterrows():
            if any('date' in str(x).lower() for x in row):
                df.columns = df.iloc[i]; return df[i+1:]
        return df
    return pd.read_excel(file)

def normalize_bank_data(df, bank_name):
    mappings = {
        'SBI': {'Txn Date': 'Date', 'Description': 'Narration', 'Debit': 'Debit', 'Credit': 'Credit'},
        'HDFC Bank': {'Date': 'Date', 'Narration': 'Narration', 'Withdrawal Amt.': 'Debit', 'Deposit Amt.': 'Credit'},
        'ICICI': {'Value Date': 'Date', 'Transaction Remarks': 'Narration', 'Withdrawal Amount (INR )': 'Debit', 'Deposit Amount (INR )': 'Credit'}
    }
    if bank_name in mappings: df = df.rename(columns=mappings[bank_name])
    for col in ['Date', 'Narration', 'Debit', 'Credit']:
        if col not in df.columns: df[col] = 0 if col in ['Debit', 'Credit'] else ""
    df['Debit'] = df['Debit'].apply(clean_currency)
    df['Credit'] = df['Credit'].apply(clean_currency)
    return df[['Date', 'Narration', 'Debit', 'Credit']]

# --- 5. MAIN NAVIGATION ---
tabs = st.tabs(["Home", "Solutions", "Pricing", "Login", "Register"])

with tabs[0]:
    if st.session_state.logged_in:
        # PROFILE BUTTON (Top Right Logic)
        col_p1, col_p2 = st.columns([10, 1])
        with col_p2:
            user_data = st.session_state.users_db[st.session_state.users_db['Username'] == st.session_state.current_user].iloc[0]
            if st.button("👤 Profile"):
                st.session_state.show_settings = not st.session_state.show_settings; st.rerun()

        if st.session_state.show_settings:
            st.markdown("## ⚙️ Account Settings")
            new_pic = st.file_uploader("Upload Profile Picture", type=['png', 'jpg'])
            new_pass = st.text_input("New Password", type="password")
            if st.button("Save Changes"):
                idx = st.session_state.users_db[st.session_state.users_db['Username'] == st.session_state.current_user].index[0]
                if new_pic: st.session_state.users_db.at[idx, 'Pic'] = new_pic
                if new_pass: st.session_state.users_db.at[idx, 'Password'] = new_pass
                st.success("Profile Updated!"); st.session_state.show_settings = False; st.rerun()
        else:
            st.markdown(f"<h1>Welcome back, {st.session_state.current_user}!</h1>", unsafe_allow_html=True)
            # --- THE ACTUAL WORK SECTION ---
            st.markdown("### 🛠️ Converter Tool (Your Work File)")
            c1, c2 = st.columns([1, 1.5], gap="large")
            with c1:
                with st.container(border=True):
                    st.markdown("#### 1. Configuration")
                    up_html = st.file_uploader("Upload Tally Master (master.html)", type=['html'])
                    ledgers = get_ledger_names(up_html) if up_html else ["Cash", "Bank", "Suspense A/c"]
                    bank_ledg = st.selectbox("Bank Ledger", ledgers)
                    part_ledg = st.selectbox("Default Party", ledgers)
            with c2:
                with st.container(border=True):
                    st.markdown("#### 2. Process File")
                    bank_choice = st.selectbox("Bank Format", ["SBI", "HDFC Bank", "ICICI", "Other"])
                    up_file = st.file_uploader("Upload Statement", type=['xlsx', 'pdf'])
                    if up_file:
                        df = load_bank_file(up_file)
                        if df is not None:
                            df_c = normalize_bank_data(df, bank_choice)
                            st.dataframe(df_c.head(3), use_container_width=True)
                            if st.button("🚀 Process & Generate XML"):
                                st.balloons(); st.success("Conversion Ready!")
    else:
        st.markdown('<h1>Perfecting the Science of Data Extraction</h1>', unsafe_allow_html=True)
        st.info("👋 Access Restricted. Please Sign In to use the tools.")

with tabs[3]:
    st.markdown("## 🔐 Sign In")
    l_u = st.text_input("Username", key="l_u")
    l_p = st.text_input("Password", type="password", key="l_p")
    if st.button("Sign In"):
        db = st.session_state.users_db
        if ((db['Username'] == l_u) & (db['Password'] == l_p)).any():
            st.session_state.logged_in = True; st.session_state.current_user = l_u; st.rerun()
        else: st.error("Invalid credentials.")

# --- 6. PINNED FOOTER ---
st.markdown(f'<div class="footer"><p>Sponsored By <b>Uday Mondal</b> | Powered & Created by <b>Debasish Biswas</b></p></div>', unsafe_allow_html=True)
