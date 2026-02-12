import streamlit as st
import pandas as pd
from bs4 import BeautifulSoup
import pdfplumber
import re
import time
import base64
import io

# --- 1. PAGE CONFIG & ORIGINAL CSS ---
st.set_page_config(
    page_title="Accounting Expert | AI Bank to Tally", 
    page_icon="logo.png",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
        
        /* Global Background */
        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif;
            background-color: #F8FAFC; 
            color: #0F172A;
        }

        /* PERSISTENT SIDEBAR DESIGN */
        .stSidebar { background-color: #0F172A !important; color: white !important; }
        .sidebar-footer { font-size: 12px; color: #64748B; text-align: center; margin-top: 50px; }

        /* HERO SECTION */
        .hero-container {
            text-align: center;
            padding: 50px 20px;
            background: linear-gradient(135deg, #065F46 0%, #1E40AF 100%);
            color: white;
            margin: -6rem -4rem 30px -4rem;
            box-shadow: 0 10px 30px -10px rgba(6, 95, 70, 0.5);
            position: relative;
        }
        
        .hero-title { font-size: 3.5rem; font-weight: 800; margin-top: 10px; }
        .hero-subtitle { font-size: 1.2rem; color: #E2E8F0; font-weight: 300; opacity: 0.9; }

        /* Card Styling */
        .stContainer {
            background-color: white;
            padding: 30px;
            border-radius: 16px;
            box-shadow: 0 4px 20px -5px rgba(0, 0, 0, 0.05);
            border: 1px solid #E2E8F0;
        }
        
        h3 { border-left: 5px solid #10B981; padding-left: 12px; font-weight: 700 !important; }

        /* Futuristic Button */
        .stButton>button {
            width: 100%;
            background: linear-gradient(90deg, #10B981 0%, #3B82F6 100%);
            color: white;
            border-radius: 8px;
            height: 55px;
            font-weight: 600;
            border: none;
            transition: all 0.3s ease;
        }
        .stButton>button:hover { transform: translateY(-2px); box-shadow: 0 8px 25px rgba(16, 185, 129, 0.4); }

        /* Footer */
        .footer {
            margin-top: 60px; padding: 40px; text-align: center;
            color: #64748B; font-size: 0.9rem; border-top: 1px solid #E2E8F0;
            background-color: white; margin-bottom: -60px;
        }
        
        #MainMenu, footer, header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- 2. HELPER FUNCTIONS ---

def get_img_as_base64(file):
    try:
        with open(file, "rb") as f: return base64.b64encode(f.read()).decode()
    except: return None

def clean_currency(value):
    if pd.isna(value) or value == '': return 0.0
    val = re.sub(r'[^\d.]', '', str(value))
    try: return float(val)
    except: return 0.0

def smart_normalize(df):
    """Prevents AttributeErrors and maps headers dynamically."""
    if df is None or df.empty: return pd.DataFrame()
    df = df.dropna(how='all').reset_index(drop=True)
    
    header_idx = None
    for i, row in df.iterrows():
        # Safeguard: Force row contents to strings before joining
        row_str = " ".join([str(v).lower() for v in row.values if v is not None])
        if 'date' in row_str and ('narration' in row_str or 'particular' in row_str or 'description' in row_str):
            header_idx = i
            break
            
    if header_idx is not None:
        df.columns = df.iloc[header_idx]
        df = df[header_idx + 1:].reset_index(drop=True)
    
    df.columns = df.columns.astype(str).str.strip().str.lower()
    new_df = pd.DataFrame()
    col_map = {
        'Date': ['date', 'txn', 'value', 'tran'],
        'Narration': ['narration', 'particular', 'description', 'remarks'],
        'Debit': ['debit', 'withdrawal', 'out', 'dr'],
        'Credit': ['credit', 'deposit', 'in', 'cr']
    }

    for target, aliases in col_map.items():
        found = next((c for c in df.columns if any(a in c for a in aliases)), None)
        if found:
            new_df[target] = df[found]
        else:
            new_df[target] = 0.0 if target in ['Debit', 'Credit'] else "UNTRACED"
            
    new_df['Debit'] = new_df['Debit'].apply(clean_currency)
    new_df['Credit'] = new_df['Credit'].apply(clean_currency)
    return new_df.dropna(subset=['Date'])

def generate_tally_xml(df, bank_ledger, party_ledger):
    """Balanced XML to fix 'No Entries' import error."""
    xml_header = """<ENVELOPE><HEADER><TALLYREQUEST>Import Data</TALLYREQUEST></HEADER><BODY><IMPORTDATA><REQUESTDESC><REPORTNAME>Vouchers</REPORTNAME></REQUESTDESC><REQUESTDATA>"""
    xml_footer = """</REQUESTDATA></IMPORTDATA></BODY></ENVELOPE>"""
    body = ""
    for _, row in df.iterrows():
        amt = row['Debit'] if row['Debit'] > 0 else row['Credit']
        if amt <= 0: continue
        vch_type = "Payment" if row['Debit'] > 0 else "Receipt"
        
        # Determine Dr/Cr based on Tally logic
        l1, l1_amt = (party_ledger, amt) if vch_type == "Payment" else (bank_ledger, amt)
        l2, l2_amt = (bank_ledger, -amt) if vch_type == "Payment" else (party_ledger, -amt)

        try: d = pd.to_datetime(row['Date'], dayfirst=True).strftime("%Y%m%d") #
        except: d = "20260401"
        nar = str(row['Narration']).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        
        body += f"""<TALLYMESSAGE xmlns:UDF="TallyUDF"><VOUCHER VCHTYPE="{vch_type}" ACTION="Create"><DATE>{d}</DATE><NARRATION>{nar}</NARRATION><VOUCHERTYPENAME>{vch_type}</VOUCHERTYPENAME><ALLLEDGERENTRIES.LIST><LEDGERNAME>{l1}</LEDGERNAME><ISDEEMEDPOSITIVE>{"Yes" if l1_amt > 0 else "No"}</ISDEEMEDPOSITIVE><AMOUNT>{-l1_amt}</AMOUNT></ALLLEDGERENTRIES.LIST><ALLLEDGERENTRIES.LIST><LEDGERNAME>{l2}</LEDGERNAME><ISDEEMEDPOSITIVE>{"Yes" if l2_amt > 0 else "No"}</ISDEEMEDPOSITIVE><AMOUNT>{-l2_amt}</AMOUNT></ALLLEDGERENTRIES.LIST></VOUCHER></TALLYMESSAGE>"""
    return xml_header + body + xml_footer

# --- 3. PERSISTENT SIDEBAR ---
with st.sidebar:
    st.title("🛡️ User Hub")
    with st.expander("👤 User Account", expanded=True):
        st.write("Logged in as: **Guest**")
    with st.expander("💳 Subscription Plans"):
        st.markdown("- **Current:** Free Tier\n- **Pro:** ₹999/mo")
    with st.expander("❓ Help & Solutions"):
        st.write("For 'No Entries' errors, ensure your Bank Ledger exists in Tally exactly as named here.")
    st.divider()
    st.markdown('<p class="sidebar-footer">Accounting Expert v2.0<br>Created by Debasish Biswas</p>', unsafe_allow_html=True)

# --- 4. MAIN DASHBOARD ---
# Main Logo rendering
hero_logo_b64 = get_img_as_base64("logo.png")
hero_logo_html = f'<img src="data:image/png;base64,{hero_logo_b64}" width="120" style="margin-bottom: 20px;">' if hero_logo_b64 else ""

st.markdown(f"""
    <div class="hero-container">
        {hero_logo_html}
        <div class="hero-title">Accounting Expert</div>
        <div class="hero-subtitle">Smart AI Bank Statement to Tally XML Converter</div>
    </div>
""", unsafe_allow_html=True)

col_left, col_right = st.columns([1, 1.5], gap="large")

with col_left:
    with st.container():
        st.markdown("### 🛠️ 1. Settings")
        master = st.file_uploader("Upload Tally Master (HTML)", type=['html', 'htm'])
        ledger_list = ["Suspense A/c", "Cash", "Bank"]
        if master:
            soup = BeautifulSoup(master, 'html.parser')
            extracted = sorted(list(set([t.text.strip() for t in soup.find_all('td') if t.text.strip()])))
            if extracted: ledger_list = extracted; st.success(f"✅ {len(ledger_list)} Ledgers Synced")
            
        bank_ledger = st.selectbox("Select Bank Ledger", ledger_list)
        party_ledger = st.selectbox("Select Default Party", ledger_list)

with col_right:
    with st.container():
        st.markdown("### 📂 2. Upload & Convert")
        stmt_file = st.file_uploader("Drop Statement here (Excel or PDF)", type=['xlsx', 'xls', 'pdf'])
        
        if stmt_file:
            with st.status("💎 AI Analysis in Progress...", expanded=False) as status:
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
                    status.update(label="✅ Analysis Complete!", state="complete")
                    st.write("**Preview:**")
                    st.dataframe(df_clean[['Date', 'Narration', 'Debit', 'Credit']].head(5), use_container_width=True)
                    
                    if st.button("🚀 GENERATE TALLY XML"):
                        st.balloons()
                        xml_data = generate_tally_xml(df_clean, bank_ledger, party_ledger)
                        st.download_button("⬇️ Download XML", xml_data, "tally_import.xml")
                else:
                    status.update(label="❌ Detection Failed", state="error")
                    st.error("Could not find headers. Check PDF layout.")

# --- 5. SPONSORED FOOTER ---
footer_logo_b64 = get_img_as_base64("logo 1.png")
footer_logo_html = f'<img src="data:image/png;base64,{footer_logo_b64}" width="25" style="vertical-align: middle;">' if footer_logo_b64 else ""

st.markdown(f"""
    <div class="footer">
        <p>Sponsored By {footer_logo_html} <b>Uday Mondal</b> | Consultant Advocate</p>
        <p style="font-size: 13px;">Created & Powered by <b>Debasish Biswas</b> | Professional Tally Automation</p>
    </div>
""", unsafe_allow_html=True)
