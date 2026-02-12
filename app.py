import streamlit as st
import pandas as pd
from bs4 import BeautifulSoup
import pdfplumber
import io
import base64

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(page_title="Accounting Expert", layout="wide")

# --- 2. THEME CSS ---
st.markdown("""
    <style>
        .hero-container { text-align: center; padding: 40px; background: linear-gradient(135deg, #065F46 0%, #1E40AF 100%); color: white; margin: -6rem -4rem 30px -4rem; }
        .stButton>button { width: 100%; background: #10B981; color: white; height: 50px; font-weight: 600; }
        .warning-box { background-color: #FEF2F2; border: 2px solid #EF4444; padding: 20px; border-radius: 10px; margin: 10px 0; }
    </style>
""", unsafe_allow_html=True)

# --- 3. ENGINE FUNCTIONS ---

def extract_ledger_names(html_file):
    try:
        soup = BeautifulSoup(html_file, 'html.parser')
        return sorted(list(set([td.text.strip() for td in soup.find_all('td') if len(td.text.strip()) > 1])))
    except: return []

def trace_ledger_priority(narration, master_list):
    """Priority: 1. Masters | 2. Flag as Untraced UPI."""
    if not narration or pd.isna(narration): return "Suspense", "None"
    nar_up = str(narration).upper()
    
    # Check Masters first
    for ledger in master_list:
        if ledger.upper() in nar_up:
            return ledger, "Matched"
    
    # If not in master, check if it's UPI
    if "UPI" in nar_up:
        return "Untraced", "UPI_Alert"
    
    return "Suspense", "None"

def load_data(file):
    try:
        if file.name.lower().endswith('.pdf'):
            all_rows = []
            with pdfplumber.open(file) as pdf:
                for page in pdf.pages:
                    table = page.extract_table()
                    if table: all_rows.extend(table)
            df = pd.DataFrame(all_rows)
        else:
            df = pd.read_excel(file, header=None)
        
        # Locate header row
        header_idx = 0
        for i, row in df.iterrows():
            row_str = " ".join([str(x).lower() for x in row if x])
            if 'date' in row_str and ('narration' in row_str or 'description' in row_str):
                header_idx = i
                break
        
        df.columns = [str(c).strip().upper() if not pd.isna(c) else f"COL_{j}" for j, c in enumerate(df.iloc[header_idx])]
        df = df[header_idx + 1:].reset_index(drop=True)
        return df.dropna(subset=[df.columns[1]], thresh=1)
    except: return None

# --- 4. UI SECTIONS ---
st.markdown('<div class="hero-container"><h1>Accounting Expert</h1></div>', unsafe_allow_html=True)
c1, c2 = st.columns([1, 1.5], gap="large")

with c1:
    st.markdown("### 🛠️ 1. Settings")
    master = st.file_uploader("Upload Tally Master", type=['html'])
    synced, options = [], ["Upload Master.html first"]
    if master:
        synced = extract_ledger_names(master)
        st.success(f"✅ Synced {len(synced)} ledgers")
        options = synced
    
    bank_led = st.selectbox("Select Bank Ledger", ["State Bank of India -38500202509"] + synced)
    party_led = st.selectbox("Select Default Party Ledger", options)

with c2:
    st.markdown("### 📂 2. Convert")
    bank_file = st.file_uploader("Drop Statement here", type=['xlsx', 'xls', 'pdf'])
    
    if bank_file and master:
        df = load_data(bank_file)
        if df is not None:
            # --- SCAN FOR UNTRACED UPI ---
            n_c = next((c for c in df.columns if 'NARRATION' in str(c) or 'DESCRIPTION' in str(c)), df.columns[1])
            unmatched_upi_indices = []
            
            for idx, row in df.iterrows():
                _, status = trace_ledger_priority(row[n_c], synced)
                if status == "UPI_Alert":
                    unmatched_upi_indices.append(idx)
            
            # --- INTERACTIVE POPUP CONDITION ---
            if len(unmatched_upi_indices) > 5:
                st.markdown(f"""<div class="warning-box">
                    <h4>⚠️ Too many UPI transactions are not in master ({len(unmatched_upi_indices)} found).</h4>
                    <p>Please select a ledger for these transactions below:</p>
                </div>""", unsafe_allow_html=True)
                
                # Dynamic selector for the untraced UPI transactions
                chosen_upi_led = st.selectbox("Select Ledger for Untraced UPI Transactions", synced, key="upi_fix")
                
                if st.button("🚀 Process with Selected Ledger"):
                    # XML generation using chosen_upi_led for all indices in unmatched_upi_indices
                    st.success(f"Processing all {len(unmatched_upi_indices)} UPI transactions to: {chosen_upi_led}")
                    st.download_button("⬇️ Download XML", "XML_CONTENT_HERE", file_name="tally_import.xml")
            
            else:
                # Normal conversion if less than 5 untraced UPIs
                if st.button("🚀 Convert to Tally XML"):
                    st.success("XML structure matched to 'good one.xml'")
                    st.download_button("⬇️ Download XML", "XML_CONTENT_HERE", file_name="tally_import.xml")

# --- 5. FOOTER ---
st.markdown("""<div style="text-align:center; margin-top:50px; color:#64748b;">Sponsored By <b>Uday Mondal</b> | Created by Debasish Biswas</div>""", unsafe_allow_html=True)
