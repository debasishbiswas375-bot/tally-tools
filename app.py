import streamlit as st
import pandas as pd
from bs4 import BeautifulSoup
import pdfplumber
import re
import time

# --- 1. PAGE CONFIG & FUTURISTIC THEME ---
st.set_page_config(page_title="Accounting Expert AI", layout="wide", page_icon="💎")

st.markdown("""
    <style>
        @keyframes cyber-pulse { 0% { box-shadow: 0 0 5px #10B981; } 50% { box-shadow: 0 0 20px #3B82F6; } 100% { box-shadow: 0 0 5px #10B981; } }
        .stButton>button { border: 1px solid #10B981; animation: cyber-pulse 3s infinite; background: #0F172A; color: white; border-radius: 12px; font-weight: 700; height: 3.5rem; }
        .loading-text { font-family: 'Courier New', monospace; color: #10B981; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# --- 2. LOGIC REPAIRS ---

def clean_currency(value):
    if pd.isna(value) or value == '': return 0.0
    val = re.sub(r'[^\d.]', '', str(value))
    try: return float(val)
    except: return 0.0

def smart_normalize(df):
    """Bulletproof normalization to prevent AttributeErrors."""
    if df is None or df.empty: return pd.DataFrame()
    df = df.dropna(how='all').reset_index(drop=True)
    
    header_idx = None
    for i, row in df.iterrows():
        # Safeguard: Convert all row elements to string safely
        row_content = [str(val).lower() for val in row.values if val is not None]
        row_str = " ".join(row_content)
        if 'date' in row_str and ('narration' in row_str or 'particular' in row_str):
            header_idx = i
            break
    
    if header_idx is not None:
        df.columns = df.iloc[header_idx]
        df = df[header_idx + 1:].reset_index(drop=True)
    
    df.columns = df.columns.astype(str).str.strip().str.lower()
    new_df = pd.DataFrame()
    col_map = {'Date': ['date'], 'Narration': ['narration', 'particular', 'desc'], 'Debit': ['debit', 'withdr', 'out'], 'Credit': ['credit', 'depo', 'in']}

    for target, aliases in col_map.items():
        found = next((c for c in df.columns if any(a in c for a in aliases)), None)
        new_df[target] = df[found] if found else (0.0 if target in ['Debit', 'Credit'] else "UNTRACED")

    new_df['Debit'] = new_df['Debit'].apply(clean_currency)
    new_df['Credit'] = new_df['Credit'].apply(clean_currency)
    return new_df.dropna(subset=['Date'])

# --- 3. UI WITH ANIMATIONS ---
st.title("🚀 Accounting Expert AI Engine")

with st.sidebar:
    st.header("Master Data")
    master = st.file_uploader("Upload Tally Master", type=['html'])
    ledgers = ["Suspense A/c"]
    if master:
        soup = BeautifulSoup(master, 'html.parser')
        ledgers = sorted(list(set([t.text.strip() for t in soup.find_all('td') if t.text.strip()])))
    bank_led = st.selectbox("Bank Ledger", ledgers)
    part_led = st.selectbox("Default Party", ledgers)

stmt = st.file_uploader("Upload Bank Statement", type=['pdf', 'xlsx'])

if stmt:
    # --- FUTURISTIC PROCESSING BAR ---
    with st.status("🛠️ AI Engine Initializing...", expanded=True) as status:
        st.write("📡 Decoding PDF Layers...")
        time.sleep(1)
        
        if stmt.name.endswith('.pdf'):
            with pdfplumber.open(stmt) as pdf:
                data = []
                for p in pdf.pages:
                    table = p.extract_table()
                    if table: data.extend(table)
            df_raw = pd.DataFrame(data)
        else:
            df_raw = pd.read_excel(stmt)

        st.write("🧠 Applying Smart Normalization...")
        df_clean = smart_normalize(df_raw)
        
        if not df_clean.empty:
            status.update(label="✅ Analysis Success!", state="complete", expanded=False)
            st.dataframe(df_clean.head(10), use_container_width=True)
            
            if st.button("GENERATE TALLY XML"):
                st.balloons()
                # Use the XML generator function here...
        else:
            status.update(label="❌ Detection Failed", state="error")
            st.error("I couldn't find the Date/Narration headers. Please check the PDF format.")
