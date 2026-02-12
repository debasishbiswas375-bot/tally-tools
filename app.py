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

# --- 2. FUTURISTIC THEME CSS ---
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
        html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #F8FAFC; color: #0F172A; }
        .hero-container { text-align: center; padding: 50px 20px; background: linear-gradient(135deg, #065F46 0%, #1E40AF 100%); color: white; margin: -6rem -4rem 30px -4rem; box-shadow: 0 10px 30px -10px rgba(6, 95, 70, 0.5); position: relative; }
        .footer { margin-top: 60px; padding: 40px; text-align: center; color: #64748B; font-size: 0.95rem; border-top: 1px solid #E2E8F0; background-color: white; margin-left: -4rem; margin-right: -4rem; margin-bottom: -6rem; }
        .brand-link { color: #059669; text-decoration: none; font-weight: 700; }
        .stButton>button { width: 100%; background: linear-gradient(90deg, #10B981 0%, #3B82F6 100%); color: white; border-radius: 8px; height: 55px; font-weight: 600; border: none; }
        #MainMenu, footer, header { visibility: hidden; }
    </style>
""", unsafe_allow_html=True)

# --- 3. HELPER & ENGINE FUNCTIONS ---

def get_img_as_base64(file):
    try:
        with open(file, "rb") as f: return base64.b64encode(f.read()).decode()
    except: return None

def extract_ledger_names(html_file):
    try:
        soup = BeautifulSoup(html_file, 'html.parser')
        ledgers = [td.text.strip() for td in soup.find_all('td') if len(td.text.strip()) > 1]
        return sorted(list(set(ledgers)))
    except: return []

# --- UPDATED: FALLBACK TO SUSPENSE LOGIC ---
def trace_ledger(remark, master_list):
    """If no match is found, always return 'Suspense'."""
    if not remark or pd.isna(remark): 
        return "Suspense"
    
    remark_up = str(remark).upper()
    for ledger in master_list:
        if ledger.upper() in remark_up: 
            return ledger
            
    return "Suspense"

def load_data(file):
    if file.name.lower().endswith('.pdf'):
        all_rows = []
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages:
                table = page.extract_table()
                if table: all_rows.extend(table)
        df = pd.DataFrame(all_rows)
        for i, row in df.iterrows():
            if any(k in str(row).lower() for k in ['date', 'txn', 'description', 'narration']):
                df.columns = df.iloc[i]
                return df[i+1:].reset_index(drop=True)
        return df
    else:
        return pd.read_excel(file)

def generate_tally_xml(df, bank_ledger, default_party, master_list):
    xml_header = """<ENVELOPE><HEADER><TALLYREQUEST>Import Data</TALLYREQUEST></HEADER><BODY><IMPORTDATA><REQUESTDESC><REPORTNAME>Vouchers</REPORTNAME></REQUESTDESC><REQUESTDATA>"""
    xml_footer = """</REQUESTDATA></IMPORTDATA></BODY></ENVELOPE>"""
    xml_body = ""
    
    df.columns = [str(c).strip() for c in df.columns]
    
    for _, row in df.iterrows():
        try:
            debit = float(str(row.get('Debit', 0)).replace(',', '')) if row.get('Debit') else 0
            credit = float(str(row.get('Credit', 0)).replace(',', '')) if row.get('Credit') else 0
            narration_raw = str(row.get('Narration', row.get('Description', '')))
            
            if debit > 0:
                vch_type, amt = "Payment", debit
                led1, led1_pos, led1_amt = (default_party, "Yes", -amt)
                led2, led2_pos, led2_amt = (bank_ledger, "No", amt)
            elif credit > 0:
                vch_type, amt = "Receipt", credit
                led1, led1_pos, led1_amt = (bank_ledger, "Yes", -amt)
                led2, led2_pos, led2_amt = (default_party, "No", amt)
            else: continue

            # ⭐ AI Tracing with Mandatory Suspense Fallback
            if "⭐" in default_party and master_list:
                traced = trace_ledger(narration_raw, master_list)
                if vch_type == "Payment": led1 = traced
                else: led2 = traced

            try: date_str = pd.to_datetime(row.get('Date', row.get('Txn Date'))).strftime("%Y%m%d")
            except: date_str = "20260401"
            
            clean_narration = narration_raw.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

            xml_body += f"""<TALLYMESSAGE xmlns:UDF="TallyUDF">
                <VOUCHER VCHTYPE="{vch_type}" ACTION="Create" OBJVIEW="Accounting Voucher View">
                <DATE>{date_str}</DATE><NARRATION>{clean_narration}</NARRATION><VOUCHERTYPENAME>{vch_type}</VOUCHERTYPENAME>
                <ALLLEDGERENTRIES.LIST><LEDGERNAME>{led1}</LEDGERNAME><ISDEEMEDPOSITIVE>{led1_pos}</ISDEEMEDPOSITIVE><AMOUNT>{led1_amt}</AMOUNT></ALLLEDGERENTRIES.LIST>
                <ALLLEDGERENTRIES.LIST><LEDGERNAME>{led2}</LEDGERNAME><ISDEEMEDPOSITIVE>{led2_pos}</ISDEEMEDPOSITIVE><AMOUNT>{led2_amt}</AMOUNT></ALLLEDGERENTRIES.LIST>
                </VOUCHER></TALLYMESSAGE>"""
        except: continue
    return xml_header + xml_body + xml_footer

# --- 4. UI DASHBOARD ---

hero_logo = get_img_as_base64("logo.png")
hero_html = f'<img src="data:image/png;base64,{hero_logo}" width="120">' if hero_logo else ""
st.markdown(f'<div class="hero-container">{hero_html}<div style="font-size:3.5rem; font-weight:800;">Accounting Expert</div></div>', unsafe_allow_html=True)

col1, col2 = st.columns([1, 1.5], gap="large")

with col1:
    st.markdown("### 🛠️ 1. Settings & Mapping")
    master_file = st.file_uploader("Upload Tally Master (Optional)", type=['html'])
    ledger_options = ["Suspense", "Cash", "Bank"]
    synced_masters = []
    if master_file:
        synced_masters = extract_ledger_names(master_file)
        st.success(f"✅ Synced {len(synced_masters)} ledgers")
        ledger_options = ["⭐ AI Auto-Trace (Premium)"] + synced_masters
    
    bank_led = st.selectbox("Select Bank Ledger", ["State Bank of India -38500202509"])
    party_led = st.selectbox("Select Default Party", ledger_options)

with col2:
    st.markdown("### 📂 2. Upload & Convert")
    bank_file = st.file_uploader("Drop Statement here (Excel or PDF)", type=['xlsx', 'pdf'])
    if bank_file:
        if st.button("🚀 Convert to Tally XML"):
            df = load_data(bank_file)
            xml_data = generate_tally_xml(df, bank_led, party_led, synced_masters)
            st.balloons()
            st.success("Premium AI Match Complete!")
            st.download_button("⬇️ Download Tally XML File", xml_data, "tally_import.xml", use_container_width=True)

# --- 5. BRANDED FOOTER ---
s_logo = get_img_as_base64("logo 1.png")
c_logo = get_img_as_base64("logo.png")
s_html = f'<img src="data:image/png;base64,{s_logo}" width="25" style="vertical-align:middle; margin-right:5px;">' if s_logo else ""
c_html = f'<img src="data:image/png;base64,{c_logo}" width="20" style="vertical-align:middle; margin-right:5px;">' if c_logo else ""

st.markdown(f"""<div class="footer">
    <p>Sponsored By {s_html} <span class="brand-link" style="color:#0F172A;">Uday Mondal</span> | Consultant Advocate</p>
    <p style="font-size: 13px;">{c_html} Powered & Created by <span class="brand-link">Debasish Biswas</span></p>
</div>""", unsafe_allow_html=True)
