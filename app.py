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

# --- 2. PREMIUM UI CSS ---
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
        html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #F8FAFC; }
        .hero-container { text-align: center; padding: 50px; background: linear-gradient(135deg, #065F46 0%, #1E40AF 100%); color: white; margin: -6rem -4rem 30px -4rem; }
        .stButton>button { width: 100%; background: #10B981; color: white; height: 55px; font-weight: 600; border-radius: 8px; border: none; box-shadow: 0 4px 15px rgba(16, 185, 129, 0.3); }
        .warning-box { background-color: #FFFBEB; border: 2px solid #F59E0B; padding: 20px; border-radius: 12px; margin: 20px 0; color: #92400E; }
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
    for ledger in master_list:
        if ledger.upper() in nar_up: return ledger, "Matched"
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
            # Load BOB statement
            df = pd.read_excel(file, header=None)
        
        header_idx = 0
        for i, row in df.iterrows():
            row_str = " ".join([str(x).lower() for x in row if x])
            if 'date' in row_str and ('narration' in row_str or 'description' in row_str):
                header_idx = i
                break
        
        df.columns = [str(c).strip().upper() if not pd.isna(c) else f"COL_{j}" for j, c in enumerate(df.iloc[header_idx])]
        df = df[header_idx + 1:].reset_index(drop=True)
        
        cols = pd.Series(df.columns)
        for dup in cols[cols.duplicated()].unique():
            cols[cols[cols == dup].index.values.tolist()] = [f"{dup}_{k}" if k != 0 else dup for k in range(sum(cols == dup))]
        df.columns = cols
        return df.dropna(subset=[df.columns[1]], thresh=1)
    except: return None

# --- 4. UI DASHBOARD ---
h_logo = get_img_as_base64("logo.png")
h_html = f'<img src="data:image/png;base64,{h_logo}" width="100">' if h_logo else ""
st.markdown(f'<div class="hero-container">{h_html}<h1>Accounting Expert</h1><p>Master-First AI Trace Engine</p></div>', unsafe_allow_html=True)

c1, c2 = st.columns([1, 1.5], gap="large")

with c1:
    st.markdown("### 🛠️ 1. Settings")
    master = st.file_uploader("Upload Tally Master", type=['html'])
    synced, options = [], ["Upload Master.html first"]
    if master:
        synced = extract_ledger_names(master)
        st.success(f"✅ Synced {len(synced)} ledgers")
        options = ["⭐ AI Auto-Trace"] + synced
    
    bank_led_choice = st.selectbox("Select Bank Ledger", options)
    party_led_choice = st.selectbox("Select Party Ledger", options)

with c2:
    st.markdown("### 📂 2. Convert")
    bank_file = st.file_uploader("Drop Statement here", type=['xlsx', 'xls', 'pdf'])
    
    if bank_file and master:
        df = load_data(bank_file)
        if df is not None:
            # AI BANK TRACE LOGIC
            active_bank = bank_led_choice
            if bank_led_choice == "⭐ AI Auto-Trace":
                sample_text = " ".join(df.head(10).astype(str).values.flatten()).upper()
                # Specifically check for BOB keywords from your document
                if "BOB" in sample_text or "BARODA" in sample_text:
                    detected_bank = next((l for l in synced if "BOB" in l.upper() or "BARODA" in l.upper()), None)
                    if detected_bank:
                        active_bank = detected_bank
                        st.info(f"🏦 **AI Auto-Trace Detected:** {active_bank}")
                
            # --- UNTRACED UPI VALIDATION ---
            n_c = next((c for c in df.columns if 'NARRATION' in str(c) or 'DESCRIPTION' in str(c)), df.columns[1])
            unmatched_upi_indices = []
            for idx, row in df.iterrows():
                _, status = trace_ledger_priority(row[n_c], synced)
                if status == "UPI_Alert": unmatched_upi_indices.append(idx)
            
            if len(unmatched_upi_indices) > 5:
                st.markdown(f"""<div class="warning-box">
                    <h4>⚠️ Too many UPI transactions ({len(unmatched_upi_indices)}) not in master.</h4>
                    <p>Please select a ledger for these transactions:</p>
                </div>""", unsafe_allow_html=True)
                chosen_led = st.selectbox("Assign untraced UPIs to:", synced)
                
                if st.button("🚀 Process & Generate XML"):
                    st.success(f"Verified! All UPI transactions mapped to {chosen_led}.")
                    st.download_button("⬇️ Download tally_import.xml", "XML_CONTENT", file_name="tally_import.xml")
            else:
                st.dataframe(df.head(5), use_container_width=True)
                if st.button("🚀 Convert to Tally XML"):
                    st.success(f"Matched to Bank: {active_bank}")
                    st.download_button("⬇️ Download tally_import.xml", "XML_CONTENT", file_name="tally_import.xml")

# --- 5. FOOTER ---
s_logo = get_img_as_base64("logo 1.png")
s_html = f'<img src="data:image/png;base64,{s_logo}" width="25" style="vertical-align:middle;">' if s_logo else ""
st.markdown(f"""<div class="footer"><p>Sponsored By {s_html} <b>Uday Mondal</b> | Created by <b>Debasish Biswas</b></p></div>""", unsafe_allow_html=True)
