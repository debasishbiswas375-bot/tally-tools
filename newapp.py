import streamlit as st
import pandas as pd
from PIL import Image
from bs4 import BeautifulSoup
import pdfplumber
import io

# --- 1. CONFIGURATION & STYLING ---
st.set_page_config(
    page_title="Accounting Expert",
    page_icon="logo.png",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600&display=swap');
        html, body, [class*="css"] { font-family: 'Poppins', sans-serif; }
        
        /* Main Brand Color: #2E86C1 */
        .brand-text { color: #2E86C1 !important; font-weight: 600; }
        
        .main-header { color: #2E86C1; font-weight: 600; font-size: 2.5rem; margin-bottom: 0px; line-height: 1.2;}
        .sub-header { color: #566573; font-size: 1.1rem; margin-bottom: 30px; }
        .step-container { background-color: #f8f9fa; padding: 20px; border-radius: 10px; border: 1px solid #e9ecef; margin-bottom: 20px; }
        .stButton>button { width: 100%; background-color: #2E86C1; color: white; border-radius: 8px; height: 50px; font-weight: 600; }
        .stButton>button:hover { background-color: #1B4F72; border-color: #1B4F72; }
        .footer { position: fixed; left: 0; bottom: 0; width: 100%; background-color: #ffffff; color: #555; text-align: center; padding: 10px; border-top: 1px solid #eee; z-index: 1000; font-size: 14px; }
        #MainMenu { visibility: hidden; } footer { visibility: hidden; }
        
        /* Sidebar Title Override */
        [data-testid="stSidebarNav"] + div h1 { color: #2E86C1; }
    </style>
""", unsafe_allow_html=True)

# --- 2. LOGIC FUNCTIONS ---

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

# --- PDF EXTRACTION ---
def extract_data_from_pdf(file, password=None):
    all_rows = []
    try:
        with pdfplumber.open(file, password=password) as pdf:
            for page in pdf.pages:
                table = page.extract_table()
                if table:
                    for row in table:
                        cleaned_row = [str(cell).replace('\n', ' ').strip() if cell else '' for cell in row]
                        if any(cleaned_row):
                            all_rows.append(cleaned_row)
        if not all_rows: return None

        df = pd.DataFrame(all_rows)
        
        header_idx = 0
        found_header = False
        for i, row in df.iterrows():
            row_str = row.astype(str).str.lower().values
            if any('date' in x for x in row_str) and \
               (any('balance' in x for x in row_str) or any('debit' in x for x in row_str) or any('withdrawal' in x for x in row_str)):
                header_idx = i
                found_header = True
                break
        
        if found_header:
            new_header = df.iloc[header_idx]
            df = df[header_idx + 1:] 
            df.columns = new_header
        return df

    except Exception as e:
        if "Password" in str(e):
            st.error("🔒 Incorrect Password!")
        else:
            st.error(f"Error processing PDF: {e}")
        return None

def load_bank_file(file, password=None):
    filename = file.name.lower()
    if filename.endswith('.pdf'):
        return extract_data_from_pdf(file, password)
    else: 
        try:
            df_temp = pd.read_excel(file, header=None, nrows=30)
            header_idx = 0
            found = False
            for i, row in df_temp.iterrows():
                row_str = row.astype(str).str.lower().values
                if any('date' in x for x in row_str) and \
                   (any('balance' in x for x in row_str) or any('debit' in x for x in row_str)):
                    header_idx = i
                    found = True
                    break
            if found:
                file.seek(0)
                return pd.read_excel(file, header=
