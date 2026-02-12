import streamlit as st
import pandas as pd
from bs4 import BeautifulSoup
import pdfplumber
import re
import base64
import io
import time

# --- 1. PAGE CONFIG ---
st.set_page_config(
    page_title="Accounting Expert | AI Bank to Tally", 
    page_icon="logo.png",
    layout="wide",
    initial_sidebar_state="expanded" 
)

# --- 2. THEME & CSS ---
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700&display=swap');
        html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #F8FAFC; }
        
        /* SIDEBAR STYLING */
        [data-testid="stSidebar"] { 
            background-color: #0F172A !important; 
            color: white !important; 
        }
        
        /* Fix sidebar text and expander visibility */
        [data-testid="stSidebar"] .stText, 
        [data-testid="stSidebar"] label, 
        [data-testid="stSidebar"] .st-expander p,
        [data-testid="stSidebar"] .st-expander span { 
            color: white !important; 
        }
        
        /* Style the expander border to make it visible */
        [data-testid="stSidebar"] .st-expander {
            border: 1px solid #334155 !important;
            background-color: rgba(255, 255, 255, 0.05) !important;
            border-radius: 8px !important;
        }

        .sidebar-logo-text { font-size: 1.5rem; font-weight: 800; color: #10B981; margin-bottom: 20px; text-align: center; }
        
        /* MAXIMIZE BUTTON FIX */
        [data-testid="stSidebarCollapsedControl"] {
            background-color: #0F172A !important;
            color: #10B981 !important;
            border-radius: 0 8px 8px 0;
            border: 1px solid #10B981;
            top: 15px;
        }

        .hero-container {
            text-align: center; padding: 50px 20px;
            background: linear-gradient(135deg, #065F46 0%, #1E40AF 100%);
            color: white; margin: -6rem -4rem 30px -4rem;
            box-shadow: 0 10px 30px -10px rgba(6, 95, 70, 0.5);
        }
        
        .stContainer { background-color: white; padding: 25px; border-radius: 16px; border: 1px solid #E2E8F0; margin-bottom: 20px; }
        h3 { border-left: 5px solid #10B981; padding-left: 12px; font-weight: 700 !important; color: #1e293b !important; }

        .stButton>button { 
            width: 100%; background: linear-gradient(90deg, #10B981, #3B82F6); 
            color: white; border-radius: 8px; height: 50px; font-weight: 700; border: none;
        }
        
        #MainMenu, footer, header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- 3. HELPER & LOGIC FUNCTIONS ---

def get_img_as_base64(file):
    try:
        with open(file, "rb") as f: return base64.b64encode(f.read()).decode()
    except: return None

def clean_currency(value):
    if pd.isna(value) or value == '' or value is None: return 0.0
    val = re.sub(r'[^\d.]', '', str(value))
    try: return float(val)
    except: return 0.0

def trace_ledger(narration, master_ledgers):
    if not narration or not master_ledgers: return None
    sorted_masters = sorted([str(m) for m in master_ledgers], key=len, reverse=True)
    for ledger in sorted_masters:
        if len(ledger) < 3: continue
        pattern = r'\b' + re.escape(ledger) + r'\b'
        if re.search(pattern, str(narration), re.IGNORECASE):
            return ledger
    return None

def smart_normalize(df):
    if df is None or df.empty: return pd.DataFrame()
    
    df = df.dropna(how='all', axis=0).reset_index(drop=True)
    
    header_idx = None
    for i, row in df.iterrows():
        clean_row = [str(v).lower().strip() for v in row.values if v is not None]
        row_str = " ".join(clean_row)
        if 'date' in row_str and ('narration' in row_str or 'particular' in row_str or 'desc' in row_str):
            header_idx = i
            break
            
    if header_idx is not None:
        df.columns = df.iloc[header_idx]
        df = df[header_idx + 1:].reset_index(drop=True)
    
    df.columns = df.columns.astype(str).str.strip().str.lower()
    new_df = pd.DataFrame()
    col_map = {
        'Date': ['date', 'txn', 'value', 'tran'],
        'Narration': ['narration', 'particular', 'description', 'remarks', 'details'],
        'Debit': ['debit', 'withdrawal', 'out', 'dr'],
        'Credit': ['credit', 'deposit', 'in', 'cr']
    }
    
    for target, aliases in col_map.items():
        found = next((c for c in df.columns if any(a in c for a in aliases)), None)
        new_df[target] = df[found] if found else (0.0 if target in ['Debit', 'Credit'] else "")
    
    new_df['Debit'] = new_df['Debit'].apply(clean_currency)
    new_df['Credit'] = new_df['Credit'].apply(clean_currency)
    return new_df.dropna(subset=['Date'])

def generate_tally_xml(df, bank_ledger):
    xml_header = """<ENVELOPE><HEADER><TALLYREQUEST>Import Data</TALLYREQUEST></HEADER><BODY><IMPORTDATA><REQUESTDESC><REPORTNAME>Vouchers</REPORTNAME></REQUESTDESC><REQUESTDATA>"""
    xml_footer = """</REQUESTDATA></IMPORTDATA></BODY></ENVELOPE>"""
    body = ""
    
    for _, row in df.iterrows():
        amt = row['Debit'] if row['Debit'] > 0 else row['Credit']
        if amt <= 0: continue
        vch_type = "Payment" if row['Debit'] > 0 else "Receipt"
        
        l1, l1_amt = (row['Final Ledger'], amt) if vch_type == "Payment" else (bank_ledger, amt)
        l2, l2_amt = (bank_ledger, -amt) if vch_type == "Payment" else (row['Final Ledger'], -amt)

        try: d = pd.to_datetime(row['Date'], dayfirst=True).strftime("%Y%m%d")
        except: d = "20260401"
        
        nar = str(row['Narration']).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        
        body += f"""<TALLYMESSAGE xmlns:UDF="TallyUDF">
         <VOUCHER VCHTYPE="{vch_type}" ACTION="Create">
          <DATE>{d}</DATE>
          <NARRATION>{nar}</NARRATION>
          <ALLLEDGERENTRIES.LIST>
           <LEDGERNAME>{l1}</LEDGERNAME>
           <AMOUNT>{-l1_amt}</AMOUNT>
          </ALLLEDGERENTRIES.LIST>
          <ALLLEDGERENTRIES.LIST>
           <LEDGERNAME>{l2}</LEDGERNAME>
           <AMOUNT>{-l2_amt}</AMOUNT>
          </ALLLEDGERENTRIES.LIST>
         </VOUCHER>
        </TALLYMESSAGE>"""
    return xml_header + body + xml_footer

# --- 4. SIDEBAR ---
with st.sidebar:
    side_logo_b64 = get_img_as_base64("logo.png")
    if side_logo_b64:
        st.markdown(f'<div style="text-align:center;"><img src="data:image/png;base64,{side_logo_b64}" width="100"></div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-logo-text">Accounting Expert</div>', unsafe_allow_html=True)
    
    with st.expander("👤 User Account", expanded=True):
        st.write("User: **Debasish**")
    
    with st.expander("❓ Help & Support"):
        st.write("WhatsApp: +91 9002043666")

# --- 5. MAIN DASHBOARD ---
hero_logo_b64 = get_img_as_base64("logo.png")
hero_logo_html = f'<img src="data:image/png;base64,{hero_logo_b64}" width="100">' if hero_logo_b64 else ""

st.markdown(f"""<div class="hero-container">{hero_logo_html}<h1 style="font-size: 2.8rem; font-weight: 800;">Accounting Expert</h1></div>""", unsafe_allow_html=True)

col_left, col_right = st.columns([1, 1.5], gap="large")

with col_left:
    with st.container():
        st.markdown("### 🛠️ 1. Settings")
        master = st.file_uploader("Upload Tally Master (HTML)", type=['html'])
        ledger_list = ["Suspense A/c"]
        if master:
            soup = BeautifulSoup(master, 'html.parser')
            ledger_list = sorted(list(set([t.text.strip() for t in soup.find_all('td') if t.text.strip()])))
        bank_led = st.selectbox("Bank Ledger", ledger_list)
        part_led = st.selectbox("Default Party", ledger_list)

with col_right:
    with st.container():
        st.markdown("### 📂 2. Conversion")
        stmt_file = st.file_uploader("Upload PDF or Excel", type=['pdf', 'xlsx'])
        if stmt_file:
            with st.status("🚀 Processing...", expanded=True) as status:
                if stmt_file.name.endswith('.pdf'):
                    with pdfplumber.open(stmt_file) as pdf:
                        data = []
                        for page in pdf.pages:
                            table = page.extract_table()
                            if table: data.extend(table)
                    df_raw = pd.DataFrame(data)
                else:
                    df_raw = pd.read_excel(stmt_file)

                df_clean = smart_normalize(df_raw)
                if not df_clean.empty and 'Date' in df_clean.columns:
                    df_clean['Final Ledger'] = df_clean['Narration'].apply(lambda x: trace_ledger(x, ledger_list) or part_led)
                    status.update(label="✅ Ready!", state="complete")
                    st.dataframe(df_clean.head(10), use_container_width=True)
                    if st.button("🚀 GENERATE XML"):
                        xml_output = generate_tally_xml(df_clean, bank_led)
                        st.download_button("⬇️ Download XML", xml_output, "tally_import.xml")
                else:
                    status.update(label="❌ Detection Failed", state="error")
                    st.error("Could not detect headers. Check your PDF format.")
