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
    initial_sidebar_state="auto" # Changed to 'auto' to return to normal behavior
)

# --- 2. UNIFIED CYBER-DARK THEME CSS ---
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700&display=swap');
        
        /* Set entire app to a solid deep navy color */
        .stApp, [data-testid="stSidebar"], .main, .stSidebarContent, html, body {
            background-color: #0F172A !important;
            font-family: 'Inter', sans-serif;
            color: #F8FAFC !important;
        }

        /* Sidebar Customization */
        [data-testid="stSidebar"] * { color: white !important; }
        .sidebar-logo-text { font-size: 1.4rem; font-weight: 800; color: #10B981; text-align: center; margin-bottom: 20px; }
        .sidebar-footer-text { font-size: 12px; color: #94A3B8; text-align: center; margin-top: 30px; }

        /* Hero Container (Original Gradient Style) */
        .hero-container {
            text-align: center; padding: 40px 20px;
            background: linear-gradient(135deg, #065F46 0%, #1E40AF 100%);
            color: white; margin: -6rem -4rem 30px -4rem;
            box-shadow: 0 10px 30px rgba(0,0,0,0.5);
        }
        
        /* Card Styling (Solid Dark Tiles) */
        .stContainer, div[data-testid="stVerticalBlock"] > div:has(div.stMarkdown) {
            background-color: #1E293B !important;
            padding: 25px; border-radius: 12px; 
            border: 1px solid #334155;
            margin-bottom: 20px;
        }

        h1, h2, h3, p, span, label { color: white !important; }
        h3 { border-left: 5px solid #10B981; padding-left: 12px; font-weight: 700 !important; }

        /* Buttons */
        .stButton>button { 
            width: 100%; background: #10B981; 
            color: white !important; border-radius: 8px; height: 50px; font-weight: 700; border: none;
        }
        .stButton>button:hover { background: #059669; }
        
        #MainMenu, footer, header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- 3. HELPER FUNCTIONS ---

def get_img_as_base64(file):
    try:
        with open(file, "rb") as f: return base64.b64encode(f.read()).decode()
    except: return None

def clean_currency(value):
    if pd.isna(value) or value == '': return 0.0
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
    """Deep Scanner to prevent empty columns and detection errors."""
    if df is None or df.empty: return pd.DataFrame()
    df = df.dropna(how='all').reset_index(drop=True)
    
    header_idx = None
    for i, row in df.iterrows():
        row_str = " ".join([str(v).lower() for v in row.values if v is not None])
        if 'date' in row_str and ('narration' in row_str or 'particular' in row_str or 'desc' in row_str):
            header_idx = i
            break
            
    if header_idx is not None:
        df.columns = df.iloc[header_idx]
        df = df[header_idx + 1:].reset_index(drop=True)
    
    df.columns = df.columns.astype(str).str.strip().str.lower()
    new_df = pd.DataFrame()
    col_map = {
        'Date': ['date', 'txn', 'value'],
        'Narration': ['narration', 'particular', 'description'],
        'Debit': ['debit', 'withdrawal', 'out', 'dr'],
        'Credit': ['credit', 'deposit', 'in', 'cr']
    }
    for target, aliases in col_map.items():
        found = next((c for c in df.columns if any(a in c for a in aliases)), None)
        new_df[target] = df[found] if found else (0.0 if target in ['Debit', 'Credit'] else "")
    return new_df.dropna(subset=['Date'])

def generate_tally_xml(df, bank_ledger):
    """Generates Tally-compliant XML with balanced entries."""
    xml_header = """<ENVELOPE><HEADER><TALLYREQUEST>Import Data</TALLYREQUEST></HEADER><BODY><IMPORTDATA><REQUESTDESC><REPORTNAME>Vouchers</REPORTNAME></REQUESTDESC><REQUESTDATA>"""
    xml_footer = """</REQUESTDATA></IMPORTDATA></BODY></ENVELOPE>"""
    body = ""
    for _, row in df.iterrows():
        amt = row['Debit'] if row['Debit'] > 0 else row['Credit']
        if amt <= 0: continue
        vch_type = "Payment" if row['Debit'] > 0 else "Receipt"
        l1, l1_amt = (row['Final Ledger'], amt) if vch_type == "Payment" else (bank_ledger, amt)
        l2, l2_amt = (bank_ledger, -amt) if vch_type == "Payment" else (row['Final Ledger'], -amt)
        try: d = pd.to_datetime(row['Date'], dayfirst=True).strftime("%Y%m%d") #
        except: d = "20260401"
        nar = str(row['Narration']).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        body += f"""<TALLYMESSAGE><VOUCHER VCHTYPE="{vch_type}" ACTION="Create"><DATE>{d}</DATE><NARRATION>{nar}</NARRATION><ALLLEDGERENTRIES.LIST><LEDGERNAME>{l1}</LEDGERNAME><AMOUNT>{-l1_amt}</AMOUNT></ALLLEDGERENTRIES.LIST><ALLLEDGERENTRIES.LIST><LEDGERNAME>{l2}</LEDGERNAME><AMOUNT>{-l2_amt}</AMOUNT></ALLLEDGERENTRIES.LIST></VOUCHER></TALLYMESSAGE>"""
    return xml_header + body + xml_footer

# --- 4. PERSISTENT SIDEBAR ---
with st.sidebar:
    side_logo_b64 = get_img_as_base64("logo.png")
    if side_logo_b64:
        st.markdown(f'<div style="text-align:center;"><img src="data:image/png;base64,{side_logo_b64}" width="120"></div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-logo-text">Accounting Expert</div>', unsafe_allow_html=True)
    
    with st.expander("👤 User Account", expanded=True):
        st.write("Status: **Online**")
        st.write("User: **Debasish**")
    
    with st.expander("💳 Solutions & Pricing"):
        st.write("Plan: **Pro Tier**")
    
    with st.expander("❓ Help & Support"):
        st.write("WhatsApp: +91 9002043666")

    # Sponsored Footer at bottom of Sidebar
    st.markdown('<div style="height: 100px;"></div>', unsafe_allow_html=True)
    footer_logo_b64 = get_img_as_base64("logo 1.png")
    footer_logo_html = f'<img src="data:image/png;base64,{footer_logo_b64}" width="20" style="vertical-align: middle;">' if footer_logo_b64 else ""
    
    st.markdown(f"""
        <div class="sidebar-footer-text">
            Sponsored By {footer_logo_html} <b>Uday Mondal</b><br>
            Consultant Advocate<br><br>
            Created & Powered by<br><b>Debasish Biswas</b><br>
            v2.1 Stable Build
        </div>
    """, unsafe_allow_html=True)

# --- 5. MAIN DASHBOARD ---
hero_logo_b64 = get_img_as_base64("logo.png")
hero_logo_html = f'<img src="data:image/png;base64,{hero_logo_b64}" width="100" style="margin-bottom:15px;">' if hero_logo_b64 else ""

st.markdown(f"""
    <div class="hero-container">
        {hero_logo_html}
        <div style="font-size: 2.8rem; font-weight: 800;">Accounting Expert</div>
        <div style="font-size: 1.1rem; opacity: 0.9;">Professional Smart AI Bank to Tally XML Automation</div>
    </div>
""", unsafe_allow_html=True)

col_left, col_right = st.columns([1, 1.5], gap="large")

with col_left:
    with st.container():
        st.markdown("### 🛠️ 1. Settings")
        master = st.file_uploader("Upload Tally Master (HTML)", type=['html'])
        ledger_list = ["Suspense A/c", "Cash", "Bank"]
        if master:
            soup = BeautifulSoup(master, 'html.parser')
            extracted = sorted(list(set([t.text.strip() for t in soup.find_all('td') if t.text.strip()])))
            if extracted: ledger_list = extracted; st.success(f"✅ {len(ledger_list)} Ledgers Synced")
        
        bank_led = st.selectbox("Bank Ledger", ledger_list)
        part_led = st.selectbox("Default Party", ledger_list)

with col_right:
    with st.container():
        st.markdown("### 📂 2. Statement Processing")
        stmt_file = st.file_uploader("Upload PDF or Excel", type=['pdf', 'xlsx'])
        
        if stmt_file:
            with st.status("🚀 Processing with AI Engine...", expanded=False) as status:
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
                    st.write("**Preview:**")
                    st.dataframe(df_clean[['Date', 'Narration', 'Final Ledger', 'Debit', 'Credit']].head(10), use_container_width=True)
                    
                    if st.button("🚀 GENERATE XML"):
                        xml = generate_tally_xml(df_clean, bank_led)
                        st.balloons()
                        st.download_button("⬇️ Download XML", xml, "tally_import.xml")
                else:
                    status.update(label="❌ Detection Failed", state="error")
                    st.error("I couldn't find the Date/Narration headers. Please check the PDF format.")
