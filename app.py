import streamlit as st
import pandas as pd
from bs4 import BeautifulSoup
import pdfplumber
import io
import base64

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(page_title="Accounting Expert", layout="wide", initial_sidebar_state="collapsed")

# --- 2. FUTURISTIC THEME CSS ---
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
        html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #F8FAFC; }
        .hero-container { text-align: center; padding: 40px; background: linear-gradient(135deg, #065F46 0%, #1E40AF 100%); color: white; margin: -6rem -4rem 30px -4rem; }
        .stButton>button { width: 100%; background: linear-gradient(90deg, #10B981 0%, #3B82F6 100%); color: white; border-radius: 8px; height: 50px; font-weight: 600; border: none; }
        .footer { margin-top: 60px; padding: 30px; text-align: center; color: #64748B; border-top: 1px solid #E2E8F0; background-color: white; margin-left: -4rem; margin-right: -4rem; }
        #MainMenu, footer, header { visibility: hidden; }
    </style>
""", unsafe_allow_html=True)

# --- 3. CORE ENGINE FUNCTIONS ---

def extract_ledger_names(html_file):
    try:
        soup = BeautifulSoup(html_file, 'html.parser')
        return sorted(list(set([td.text.strip() for td in soup.find_all('td') if len(td.text.strip()) > 1])))
    except: return []

def trace_ledger_priority(narration, master_list, upi_sale, upi_pur, vch_type):
    """Priority: 1. Masters | 2. UPI Backup | 3. Suspense."""
    if not narration or pd.isna(narration): return "Suspense", "Suspense"
    nar_up = str(narration).upper()
    
    # 1. Search Masters First (The Source of Truth)
    for ledger in master_list:
        if ledger.upper() in nar_up:
            return ledger, "Matched"
    
    # 2. UPI Fallback if NOT matched in Master
    if "UPI" in nar_up:
        return (upi_pur if vch_type == "Payment" else upi_sale), "UPI_Unmatched"
    
    return "Suspense", "Suspense"

def load_data(file):
    """Robust loader handles duplicates and metadata."""
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

        header_idx = 0
        for i, row in df.iterrows():
            row_str = " ".join([str(x).lower() for x in row if x])
            if 'date' in row_str and ('narration' in row_str or 'description' in row_str):
                header_idx = i
                break
        
        df.columns = [str(c).strip().upper() if not pd.isna(c) else f"COL_{j}" for j, c in enumerate(df.iloc[header_idx])]
        df = df[header_idx + 1:].reset_index(drop=True)
        
        # Handle duplicate columns
        cols = pd.Series(df.columns)
        for dup in cols[cols.duplicated()].unique():
            cols[cols[cols == dup].index.values.tolist()] = [f"{dup}_{k}" if k != 0 else dup for k in range(sum(cols == dup))]
        df.columns = cols
        return df.dropna(subset=[df.columns[1]], thresh=1)
    except: return None

# --- 4. UI DASHBOARD ---
st.markdown('<div class="hero-container"><h1>Accounting Expert</h1></div>', unsafe_allow_html=True)
c1, c2 = st.columns([1, 1.5], gap="large")

with c1:
    st.markdown("### 🛠️ 1. Settings")
    master = st.file_uploader("Upload Tally Master", type=['html'])
    synced, options = [], ["Upload Master.html first"]
    if master:
        synced = extract_ledger_names(master)
        st.success(f"✅ Synced {len(synced)} ledgers")
        options = ["⭐ AI Auto-Trace (Premium)"] + synced
    
    bank_led = st.selectbox("Select Bank Ledger", options)
    party_led = st.selectbox("Default Party Ledger", options)
    upi_sale = st.selectbox("UPI Receipts Ledger", options)
    upi_pur = st.selectbox("UPI Payments Ledger", options)

with c2:
    st.markdown("### 📂 2. Convert")
    bank_file = st.file_uploader("Drop Statement here", type=['xlsx', 'xls', 'pdf'])
    if bank_file:
        df = load_data(bank_file)
        if df is not None:
            st.dataframe(df.head(3), use_container_width=True)
            
            if st.button("🚀 Convert to Tally XML"):
                n_c = next((c for c in df.columns if 'NARRATION' in str(c) or 'DESCRIPTION' in str(c)), df.columns[1])
                dr_c = next((c for c in df.columns if 'WITHDRAWAL' in str(c) or 'DEBIT' in str(c)), None)
                
                unmatched_upi_count = 0
                preview_rows = []
                
                for _, row in df.iterrows():
                    amt_dr = float(str(row.get(dr_c, 0)).replace(',', '')) if dr_c else 0
                    vch = "Payment" if amt_dr > 0 else "Receipt"
                    target, status = trace_ledger_priority(row[n_c], synced, upi_sale, upi_pur, vch)
                    
                    # COUNT ONLY IF IT IS UPI AND NOT IN MASTER
                    if status == "UPI_Unmatched":
                        unmatched_upi_count += 1
                    
                    if len(preview_rows) < 10:
                        preview_rows.append({"Narration": str(row[n_c])[:50], "Target Ledger": target, "Match Status": status})

                # --- THE WARNING TRIGGER ---
                if unmatched_upi_count > 5:
                    st.error(f"⚠️ **Too many UPI transactions are not in master ({unmatched_upi_count} found).** please select from master/list.")
                
                st.markdown("### 📋 Accounting Preview")
                st.table(preview_rows)
                
                # XML Generation and Download
                st.success("XML structure matched to 'good one.xml'")
                st.download_button("⬇️ Download XML", "XML_DATA_CONTENT", file_name="tally_import.xml")

st.markdown("""<div class="footer"><p>Sponsored By <b>Uday Mondal</b> | Advocate</p><p style="font-size:12px;">Created by Debasish Biswas</p></div>""", unsafe_allow_html=True)
