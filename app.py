import streamlit as st
import pandas as pd
from PIL import Image
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

# --- 2. FUTURISTIC THEME CSS (UNCHANGED) ---
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
        html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #F8FAFC; color: #0F172A; }
        .hero-container { text-align: center; padding: 50px 20px; background: linear-gradient(135deg, #065F46 0%, #1E40AF 100%); color: white; margin: -6rem -4rem 30px -4rem; box-shadow: 0 10px 30px -10px rgba(6, 95, 70, 0.5); position: relative; overflow: hidden; }
        .hero-title { font-size: 3.5rem; font-weight: 800; margin-top: 10px; text-shadow: 0 4px 10px rgba(0,0,0,0.3); }
        .hero-subtitle { font-size: 1.2rem; color: #E2E8F0; font-weight: 300; opacity: 0.9; }
        .stContainer { background-color: white; padding: 30px; border-radius: 16px; box-shadow: 0 4px 20px -5px rgba(0, 0, 0, 0.05); border: 1px solid #E2E8F0; }
        h3 { font-size: 1.2rem !important; font-weight: 700 !important; color: #1e293b !important; border-left: 5px solid #10B981; padding-left: 12px; }
        .stButton>button { width: 100%; background: linear-gradient(90deg, #10B981 0%, #3B82F6 100%); color: white; border-radius: 8px; height: 55px; font-size: 1rem; font-weight: 600; border: none; box-shadow: 0 4px 15px rgba(16, 185, 129, 0.3); transition: all 0.3s ease; }
        .footer { margin-top: 60px; padding: 40px; text-align: center; color: #64748B; font-size: 0.9rem; border-top: 1px solid #E2E8F0; background-color: white; margin-bottom: -60px; }
        #MainMenu, footer, header { visibility: hidden; }
    </style>
""", unsafe_allow_html=True)

# --- 3. HELPER FUNCTIONS ---

def get_img_as_base64(file):
    try:
        with open(file, "rb") as f: return base64.b64encode(f.read()).decode()
    except: return None

def get_ledger_names(html_file):
    try:
        soup = BeautifulSoup(html_file, 'html.parser')
        ledgers = [td.text.strip() for td in soup.find_all('td') if len(td.text.strip()) > 1]
        return sorted(list(set(ledgers)))
    except: return []

def trace_ledger(remark, master_list):
    if not remark or pd.isna(remark): return "Suspense A/c"
    remark_up = str(remark).upper()
    for ledger in master_list:
        if ledger.upper() in remark_up: return ledger
    return "Suspense A/c"

def clean_currency(value):
    if pd.isna(value) or value == '': return 0.0
    try: return float(str(value).replace(',', '').strip())
    except: return 0.0

# --- 4. RESTORED TALLY XML ENGINE ---

def generate_tally_xml(df, bank_ledger, default_party_ledger, master_list):
    xml_header = """<ENVELOPE>
    <HEADER><TALLYREQUEST>Import Data</TALLYREQUEST></HEADER>
    <BODY><IMPORTDATA><REQUESTDESC><REPORTNAME>Vouchers</REPORTNAME></REQUESTDESC><REQUESTDATA>"""
    
    xml_footer = """</REQUESTDATA></IMPORTDATA></BODY></ENVELOPE>"""
    
    xml_body = ""
    for _, row in df.iterrows():
        debit = clean_currency(row.get('Debit', 0))
        credit = clean_currency(row.get('Credit', 0))
        
        # Determine Voucher Type & Amounts
        if debit > 0:
            vch_type = "Payment"
            amount = debit
            # Party is debited (negative in Tally XML), Bank is credited (positive)
            p_led, p_amt = (default_party_ledger, -amount)
            b_led, b_amt = (bank_ledger, amount)
        elif credit > 0:
            vch_type = "Receipt"
            amount = credit
            # Bank is debited (negative), Party is credited (positive)
            b_led, b_amt = (bank_ledger, -amount)
            p_led, p_amt = (default_party_ledger, amount)
        else: continue

        # AI Trace Logic
        if "⭐" in default_party_ledger and master_list:
            p_led = trace_ledger(row.get('Narration', ''), master_list)

        try:
            date_obj = pd.to_datetime(row.get('Date'), dayfirst=True)
            date_str = date_obj.strftime("%Y%m%d")
        except: date_str = "20240401"

        narration = str(row.get('Narration', '')).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

        xml_body += f"""
        <TALLYMESSAGE xmlns:UDF="TallyUDF">
            <VOUCHER VCHTYPE="{vch_type}" ACTION="Create" OBJVIEW="Accounting Voucher View">
                <DATE>{date_str}</DATE>
                <VOUCHERTYPENAME>{vch_type}</VOUCHERTYPENAME>
                <NARRATION>{narration}</NARRATION>
                <ALLLEDGERENTRIES.LIST>
                    <LEDGERNAME>{p_led}</LEDGERNAME>
                    <ISDEEMEDPOSITIVE>{"Yes" if p_amt < 0 else "No"}</ISDEEMEDPOSITIVE>
                    <AMOUNT>{p_amt}</AMOUNT>
                </ALLLEDGERENTRIES.LIST>
                <ALLLEDGERENTRIES.LIST>
                    <LEDGERNAME>{b_led}</LEDGERNAME>
                    <ISDEEMEDPOSITIVE>{"Yes" if b_amt < 0 else "No"}</ISDEEMEDPOSITIVE>
                    <AMOUNT>{b_amt}</AMOUNT>
                </ALLLEDGERENTRIES.LIST>
            </VOUCHER>
        </TALLYMESSAGE>"""
        
    return xml_header + xml_body + xml_footer

# --- 5. UI COMPONENTS ---

hero_logo_b64 = get_img_as_base64("logo.png")
hero_logo_html = f'<img src="data:image/png;base64,{hero_logo_b64}" width="120">' if hero_logo_b64 else ""

st.markdown(f'<div class="hero-container">{hero_logo_html}<div class="hero-title">Accounting Expert</div><div class="hero-subtitle">Turn messy Bank Statements into Tally Vouchers in seconds.</div></div>', unsafe_allow_html=True)

col_left, col_right = st.columns([1, 1.5], gap="large")

with col_left:
    st.markdown("### 🛠️ 1. Settings & Mapping")
    uploaded_html = st.file_uploader("Upload Tally Master (Optional)", type=['html', 'htm'])
    ledger_options = ["Suspense A/c", "Cash", "Bank"]
    synced_masters = []
    
    if uploaded_html:
        synced_masters = get_ledger_names(uploaded_html)
        if synced_masters:
            st.success(f"✅ Synced {len(synced_masters)} ledgers")
            ledger_options = ["⭐ AI Auto-Trace (Premium)"] + synced_masters
    
    bank_ledger = st.selectbox("Select Bank Ledger", ledger_options)
    party_ledger = st.selectbox("Select Default Party", ledger_options)

with col_right:
    st.markdown("### 📂 2. Upload & Convert")
    bank_choice = st.selectbox("Select Bank Format", ["SBI", "PNB", "ICICI", "HDFC"])
    uploaded_file = st.file_uploader("Drop Statement here", type=['xlsx', 'xls', 'pdf'])
    
    if uploaded_file:
        # Simplified loading for brevity
        df_clean = pd.read_excel(uploaded_file) if not uploaded_file.name.endswith('.pdf') else pd.DataFrame()
        
        if not df_clean.empty:
            st.dataframe(df_clean.head(3), use_container_width=True)
            if st.button("🚀 Convert to Tally XML"):
                xml_data = generate_tally_xml(df_clean, bank_ledger, party_ledger, synced_masters)
                st.balloons()
                st.success("Conversion Successful!")
                st.download_button("⬇️ Download Tally XML File", xml_data, "tally_import.xml", "application/xml", use_container_width=True)
