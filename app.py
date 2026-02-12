import streamlit as st
import pandas as pd
from bs4 import BeautifulSoup
import pdfplumber
import re
import base64
import io

# --- 1. PAGE CONFIG ---
st.set_page_config(
    page_title="Accounting Expert | AI Bank to Tally", 
    page_icon="logo.png",
    layout="wide",
    initial_sidebar_state="collapsed" 
)

# --- 2. THE UI ENGINE: HARD OVERRIDE CSS ---
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700&display=swap');
        html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #F8FAFC; }
        
        /* 1. FORCE HIDE STREAMLIT DEFAULTS */
        header, footer, .stDeployButton { visibility: hidden !important; display: none !important; }

        /* 2. STYLISH FLOATING SIDEBAR TOGGLE (LEFT) */
        [data-testid="stSidebarCollapsedControl"] {
            background: linear-gradient(135deg, #10B981 0%, #059669 100%) !important;
            color: white !important;
            width: 55px !important;
            height: 55px !important;
            border-radius: 50% !important;
            top: 20px !important;
            left: 20px !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            box-shadow: 0 4px 15px rgba(16, 185, 129, 0.4) !important;
            z-index: 9999999 !important;
            border: 2px solid white !important;
            position: fixed !important;
        }
        [data-testid="stSidebarCollapsedControl"] svg { fill: white !important; width: 30px !important; height: 30px !important; }

        /* 3. PROFILE ICON (TOP RIGHT) - NO BLACK BOX */
        .user-mgmt-container {
            position: fixed; top: 20px; right: 25px; z-index: 9999999;
            display: flex; flex-direction: column; align-items: flex-end;
        }
        .profile-pic {
            width: 55px; height: 55px; border-radius: 50%;
            border: 2px solid #10B981; background-color: white;
            cursor: pointer; box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            object-fit: cover; transition: transform 0.2s;
        }
        .profile-pic:hover { transform: scale(1.05); }

        /* 4. DROPDOWN MENU */
        .user-dropdown {
            display: none; width: 220px; background: white;
            border-radius: 12px; box-shadow: 0 12px 30px rgba(0,0,0,0.2);
            padding: 18px; margin-top: 12px; border: 1px solid #E2E8F0;
            text-align: left;
        }
        .user-mgmt-container:hover .user-dropdown { display: block; }
        
        .user-dropdown h4 { color: #0F172A; margin: 0; font-size: 16px; font-weight: 700; }
        .user-dropdown p { color: #10B981; font-size: 13px; margin: 2px 0 15px 0; font-weight: 600; }
        
        .menu-item {
            display: block; padding: 10px 0; color: #334155 !important;
            font-size: 14px; text-decoration: none; border-bottom: 1px solid #F1F5F9;
            cursor: pointer; transition: 0.2s;
        }
        .menu-item:hover { color: #10B981 !important; padding-left: 8px; }

        /* HERO & SIDEBAR FIXES */
        [data-testid="stSidebar"] { background-color: #0F172A !important; }
        [data-testid="stSidebar"] * { color: white !important; }
        .hero-container {
            text-align: center; padding: 50px 20px;
            background: linear-gradient(135deg, #065F46 0%, #1E40AF 100%);
            color: white; margin: -6rem -4rem 30px -4rem;
        }
        @media (max-width: 768px) { .hero-container { margin: -6rem -2rem 20px -2rem; } }
    </style>
""", unsafe_allow_html=True)

# --- 3. INJECT CUSTOM HEADER HTML ---
st.markdown(f"""
    <div class="user-mgmt-container">
        <img src="https://www.w3schools.com/howto/img_avatar.png" class="profile-pic">
        <div class="user-dropdown">
            <h4>Debasish</h4>
            <p>Professional Tier</p>
            <div class="menu-item">🔑 Change Password</div>
            <div class="menu-item">🖼️ Update Picture</div>
            <div class="menu-item">⚡ Upgrade Tier</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# --- 4. LOGIC FUNCTIONS ---
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
    col_map = {'Date':['date','txn','value'],'Narration':['narration','particular','desc'],'Debit':['debit','withdrawal','dr'],'Credit':['credit','deposit','cr']}
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
        body += f"""<TALLYMESSAGE><VOUCHER VCHTYPE="{vch_type}" ACTION="Create"><DATE>{d}</DATE><NARRATION>{nar}</NARRATION><ALLLEDGERENTRIES.LIST><LEDGERNAME>{l1}</LEDGERNAME><AMOUNT>{-l1_amt}</AMOUNT></ALLLEDGERENTRIES.LIST><ALLLEDGERENTRIES.LIST><LEDGERNAME>{l2}</LEDGERNAME><AMOUNT>{-l2_amt}</AMOUNT></ALLLEDGERENTRIES.LIST></VOUCHER></TALLYMESSAGE>"""
    return xml_header + body + xml_footer

# --- 5. SIDEBAR ---
with st.sidebar:
    st.markdown('<div class="sidebar-logo-text">Accounting Expert</div>', unsafe_allow_html=True)
    with st.expander("👤 User Account", expanded=True):
        st.write(f"User: **Debasish**")
    with st.expander("❓ Help & Support"):
        st.write("WhatsApp: +91 9002043666")

# --- 6. MAIN DASHBOARD ---
st.markdown(f"""<div class="hero-container"><h1 style="font-size: 2.5rem; font-weight: 800;">Accounting Expert</h1></div>""", unsafe_allow_html=True)

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
            if not df_clean.empty:
                df_clean['Final Ledger'] = df_clean['Narration'].apply(lambda x: trace_ledger(x, ledger_list) or part_led)
                st.dataframe(df_clean.head(10), use_container_width=True)
                if st.button("🚀 GENERATE XML"):
                    xml_output = generate_tally_xml(df_clean, bank_led)
                    st.download_button("⬇️ Download XML", xml_output, "tally_import.xml")
