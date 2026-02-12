import streamlit as st
import pandas as pd
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

# --- 2. PREMIUM UI & FOOTER STYLING ---
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
        html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #F8FAFC; }
        .hero-container { text-align: center; padding: 50px; background: linear-gradient(135deg, #065F46 0%, #1E40AF 100%); color: white; margin: -6rem -4rem 30px -4rem; }
        .bank-detect-box { background-color: #E0F2FE; border: 2px solid #3B82F6; padding: 15px; border-radius: 10px; color: #1E3A8A; font-weight: 700; margin-bottom: 20px; text-align: center; font-size: 1.1rem; }
        .warning-box { background-color: #FEF2F2; border: 2px solid #EF4444; padding: 20px; border-radius: 12px; margin: 20px 0; color: #991B1B; }
        .preview-header { color: #1E293B; font-weight: 700; margin-top: 20px; border-bottom: 2px solid #E2E8F0; padding-bottom: 5px; }
        .stButton>button { width: 100%; background: #10B981; color: white; height: 55px; font-weight: 600; border-radius: 8px; border: none; box-shadow: 0 4px 15px rgba(16, 185, 129, 0.3); }
        .footer { margin-top: 60px; padding: 40px; text-align: center; color: #64748B; border-top: 1px solid #E2E8F0; background-color: white; margin-left: -4rem; margin-right: -4rem; }
        #MainMenu, footer, header { visibility: hidden; }
    </style>
""", unsafe_allow_html=True)

# --- 3. CORE ENGINE FUNCTIONS ---

def get_img_as_base64(file):
    try:
        with open(file, "rb") as f: return base64.b64encode(f.read()).decode()
    except: return None

def extract_ledger_names(html_file):
    try:
        soup = BeautifulSoup(html_file, 'html.parser')
        return sorted(list(set([td.text.strip() for td in soup.find_all('td') if len(td.text.strip()) > 1])))
    except: return []

def trace_ledger_priority(narration, master_list):
    if not narration or pd.isna(narration): return "Suspense", "None"
    nar_up = str(narration).upper()
    # 1. Search Master List First
    for ledger in master_list:
        if ledger.upper() in nar_up: return ledger, "Matched"
    # 2. Flag for UPI Alert
    if "UPI" in nar_up: return "Untraced", "UPI_Alert"
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

# --- 4. UI DASHBOARD ---
h_logo = get_img_as_base64("logo.png")
h_html = f'<img src="data:image/png;base64,{h_logo}" width="100">' if h_logo else ""
st.markdown(f'<div class="hero-container">{h_html}<h1>Accounting Expert</h1><p>BOB 138 Automatic Detection & Match</p></div>', unsafe_allow_html=True)

c1, c2 = st.columns([1, 1.5], gap="large")

with c1:
    st.markdown("### 🛠️ 1. Settings")
    master_file = st.file_uploader("Upload Tally Master", type=['html'])
    synced, options = [], ["Upload Master first"]
    if master_file:
        synced = extract_ledger_names(master_file)
        st.success(f"✅ Synced {len(synced)} ledgers")
        options = ["⭐ Auto-Select Bank"] + synced
    
    bank_choice = st.selectbox("Select Bank Ledger", options)
    party_choice = st.selectbox("Select Party Ledger", ["⭐ AI Auto-Trace"] + (synced if synced else []))

with c2:
    st.markdown("### 📂 2. Convert")
    bank_file = st.file_uploader("Drop Statement here", type=['xlsx', 'xls', 'pdf'])
    
    if bank_file and master_file:
        df = load_data(bank_file)
        if df is not None:
            # --- AUTO-BANK DETECTION ---
            active_bank = bank_choice
            meta_text = " ".join(df.head(20).astype(str).values.flatten()).upper()
            if bank_choice == "⭐ Auto-Select Bank" and any(k in meta_text for k in ["BOB", "BARODA", "138"]):
                active_bank = next((l for l in synced if any(k in l.upper() for k in ["BOB", "BARODA", "138"])), bank_choice)
                st.markdown(f'<div class="bank-detect-box">🏦 Auto-Detected: {active_bank}</div>', unsafe_allow_html=True)

            # --- UPI INTERACTION SCAN ---
            n_col = next((c for c in df.columns if 'NARRATION' in str(c) or 'DESCRIPTION' in str(c)), df.columns[1])
            unmatched_upi_rows = [idx for idx, row in df.iterrows() if trace_ledger_priority(row[n_col], synced)[1] == "UPI_Alert"]
            
            if len(unmatched_upi_rows) > 5:
                st.markdown(f"""<div class="warning-box">
                    <h4>⚠️ Interaction Required</h4>
                    <p>Found {len(unmatched_upi_rows)} UPI transactions not in Master.html. Please select a ledger for these entries:</p>
                </div>""", unsafe_allow_html=True)
                
                upi_fix = st.selectbox("Assign untraced UPIs to:", synced)
                
                if st.button("🚀 Process & Generate Tally XML"):
                    st.markdown('<div class="preview-header">📋 Accounting Preview (Actual Ledgers)</div>', unsafe_allow_html=True)
                    preview_data = [{"Narration": str(df.loc[i, n_col])[:50], "Target Ledger": upi_fix} for i in unmatched_upi_rows[:10]]
                    st.table(preview_data)
                    st.download_button("⬇️ Download tally_import.xml", "XML_CONTENT", file_name="tally_import.xml")
            
            else:
                # Normal conversion if matches are found
                st.dataframe(df.head(5), use_container_width=True)
                if st.button("🚀 Convert to Tally XML"):
                    st.markdown('<div class="preview-header">📋 Accounting Preview (Actual Ledgers)</div>', unsafe_allow_html=True)
                    preview_data = [{"Narration": str(row[n_col])[:50], "Target Ledger": trace_ledger_priority(row[n_col], synced)[0]} for _, row in df.head(10).iterrows()]
                    st.table(preview_data)
                    st.success(f"Conversion Ready using {active_bank}!")
                    st.download_button("⬇️ Download tally_import.xml", "XML_CONTENT", file_name="tally_import.xml")

# --- 5. FOOTER ---
s_logo = get_img_as_base64("logo 1.png")
s_html = f'<img src="data:image/png;base64,{s_logo}" width="25" style="vertical-align:middle; margin-right:5px;">' if s_logo else ""
st.markdown(f"""<div class="footer"><p>Sponsored By {s_html} <b>Uday Mondal</b> | Consultant Advocate</p><p style="font-size: 13px;">Powered & Created by <b>Debasish Biswas</b></p></div>""", unsafe_allow_html=True)
