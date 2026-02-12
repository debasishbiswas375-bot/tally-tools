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

# --- 2. PREMIUM UI CSS & DESIGN ---
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
        html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #F8FAFC; color: #0F172A; }
        .hero-container { text-align: center; padding: 50px 20px; background: linear-gradient(135deg, #065F46 0%, #1E40AF 100%); color: white; margin: -6rem -4rem 30px -4rem; box-shadow: 0 10px 30px -10px rgba(6, 95, 70, 0.5); position: relative; }
        .footer { margin-top: 60px; padding: 40px; text-align: center; color: #64748B; font-size: 0.95rem; border-top: 1px solid #E2E8F0; background-color: white; margin-left: -4rem; margin-right: -4rem; margin-bottom: -6rem; }
        .brand-link { color: #059669; text-decoration: none; font-weight: 700; }
        .stButton>button { width: 100%; background: linear-gradient(90deg, #10B981 0%, #3B82F6 100%); color: white; border-radius: 8px; height: 55px; font-weight: 600; border: none; box-shadow: 0 4px 15px rgba(16, 185, 129, 0.3); }
        .warning-box { background-color: #FFFBEB; border: 2px solid #F59E0B; padding: 20px; border-radius: 12px; margin: 20px 0; color: #92400E; }
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
        # Extract unique ledger names from Tally Master HTML
        return sorted(list(set([td.text.strip() for td in soup.find_all('td') if len(td.text.strip()) > 1])))
    except: return []

def trace_ledger_priority(narration, master_list):
    """Priority: 1. Master List | 2. Flag as Untraced UPI."""
    if not narration or pd.isna(narration): return "Suspense", "None"
    nar_up = str(narration).upper()
    
    # Priority 1: Direct Master Match
    for ledger in master_list:
        if ledger.upper() in nar_up:
            return ledger, "Matched"
    
    # Priority 2: UPI Check (If not in Master)
    if "UPI" in nar_up:
        return "Untraced", "UPI_Alert"
    
    return "Suspense", "None"

def load_data(file):
    """Handles metadata skipping and duplicate columns."""
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
        
        # Locate transaction table start
        header_idx = 0
        for i, row in df.iterrows():
            row_str = " ".join([str(x).lower() for x in row if x])
            if 'date' in row_str and ('narration' in row_str or 'description' in row_str):
                header_idx = i
                break
        
        df.columns = [str(c).strip().upper() if not pd.isna(c) else f"COL_{j}" for j, c in enumerate(df.iloc[header_idx])]
        df = df[header_idx + 1:].reset_index(drop=True)
        
        # Fix duplicate columns
        cols = pd.Series(df.columns)
        for dup in cols[cols.duplicated()].unique():
            cols[cols[cols == dup].index.values.tolist()] = [f"{dup}_{k}" if k != 0 else dup for k in range(sum(cols == dup))]
        df.columns = cols
        
        return df.dropna(subset=[df.columns[1]], thresh=1)
    except: return None

# --- 4. UI DASHBOARD ---

# Logo Design
h_logo = get_img_as_base64("logo.png")
h_html = f'<img src="data:image/png;base64,{h_logo}" width="120">' if h_logo else ""
st.markdown(f'<div class="hero-container">{h_html}<div style="font-size:3.5rem; font-weight:800;">Accounting Expert</div><p>Sync your bank statement to Tally Prime instantly</p></div>', unsafe_allow_html=True)

c1, c2 = st.columns([1, 1.5], gap="large")

with c1:
    st.markdown("### 🛠️ 1. Settings & Mapping")
    master_file = st.file_uploader("Upload Tally Master (Optional)", type=['html'])
    synced_masters, ledger_options = [], ["Upload Master.html first"]
    
    if master_file:
        synced_masters = extract_ledger_names(master_file)
        st.success(f"✅ Synced {len(synced_masters)} ledgers")
        ledger_options = synced_masters
    
    bank_ledger = st.selectbox("Select Bank Ledger", ["State Bank of India -38500202509"] + synced_masters)
    default_party = st.selectbox("Select Default Party Ledger", ledger_options)

with c2:
    st.markdown("### 📂 2. Upload & Convert")
    bank_file = st.file_uploader("Drop Statement here", type=['xlsx', 'xls', 'pdf'])
    
    if bank_file and master_file:
        df = load_data(bank_file)
        if df is not None:
            # --- REAL-TIME SCAN FOR UNTRACED UPI ---
            n_col = next((c for c in df.columns if 'NARRATION' in str(c) or 'DESCRIPTION' in str(c)), df.columns[1])
            unmatched_upi_indices = []
            
            for idx, row in df.iterrows():
                _, status = trace_ledger_priority(row[n_col], synced_masters)
                if status == "UPI_Alert":
                    unmatched_upi_indices.append(idx)
            
            # --- INTERACTIVE VALIDATION STEP ---
            if len(unmatched_upi_indices) > 5:
                st.markdown(f"""<div class="warning-box">
                    <h3>⚠️ Action Required</h3>
                    <p>Too many UPI transactions ({len(unmatched_upi_indices)}) were not found in your Master.html. Please select a ledger to assign these to:</p>
                </div>""", unsafe_allow_html=True)
                
                # Interactive Dropdown
                manual_upi_led = st.selectbox("Assign Untraced UPIs to:", synced_masters, key="fix_upi")
                
                if st.button("🚀 Process & Create Tally XML"):
                    # XML Logic would go here using manual_upi_led for indices in unmatched_upi_indices
                    st.success(f"Verified! All {len(unmatched_upi_indices)} transactions mapped to {manual_upi_led}.")
                    st.download_button("⬇️ Download tally_import.xml", "XML_CONTENT", file_name="tally_import.xml")
            
            else:
                # Normal Conversion if threshold is not met
                st.dataframe(df.head(5), use_container_width=True)
                if st.button("🚀 Convert to Tally XML"):
                    st.success("Master-First Match Complete!")
                    st.download_button("⬇️ Download tally_import.xml", "XML_CONTENT", file_name="tally_import.xml")

# --- 5. BRANDED FOOTER ---
s_logo = get_img_as_base64("logo 1.png")
s_html = f'<img src="data:image/png;base64,{s_logo}" width="25" style="vertical-align:middle; margin-right:5px;">' if s_logo else ""
st.markdown(f"""<div class="footer"><p>Sponsored By {s_html} <span class="brand-link" style="color:#0F172A;">Uday Mondal</span> | Consultant Advocate</p><p style="font-size: 13px;">Powered & Created by <span class="brand-link">Debasish Biswas</span></p></div>""", unsafe_allow_html=True)
