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

# --- 2. FUTURISTIC THEME CSS (UNCHANGED) ---
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

def trace_ledger(text, master_list):
    if not text or pd.isna(text): return "Suspense"
    text_up = str(text).upper()
    for ledger in master_list:
        if ledger.upper() in text_up: return ledger
    return "Suspense"

def load_data(file):
    fname = file.name.lower()
    try:
        if fname.endswith('.pdf'):
            all_rows = []
            with pdfplumber.open(file) as pdf:
                for page in pdf.pages:
                    table = page.extract_table()
                    if table: all_rows.extend(table)
            df = pd.DataFrame(all_rows)
        else:
            df = pd.read_excel(file)
        
        # Smart Column Detection
        for i, row in df.iterrows():
            row_str = " ".join([str(x).lower() for x in row if x])
            if 'date' in row_str and ('description' in row_str or 'narration' in row_str):
                df.columns = df.iloc[i]
                return df[i+1:].reset_index(drop=True)
        return df
    except Exception as e:
        st.error(f"Error reading statement: {e}")
        return None

def generate_tally_xml(df, bank_led_sel, party_led_sel, master_list):
    """Produces exact structure of 'good one.xml'."""
    xml_header = """<ENVELOPE><HEADER><TALLYREQUEST>Import Data</TALLYREQUEST></HEADER><BODY><IMPORTDATA><REQUESTDESC><REPORTNAME>Vouchers</REPORTNAME></REQUESTDESC><REQUESTDATA>"""
    xml_footer = """</REQUESTDATA></IMPORTDATA></BODY></ENVELOPE>"""
    xml_body = ""
    
    # Trace Bank from file content if Auto-Trace is chosen
    actual_bank = bank_led_sel
    if "⭐" in bank_led_sel and master_list:
        # Check first few rows/headers for bank keywords
        found_bank = trace_ledger(str(df.iloc[0:2]), master_list)
        if found_bank != "Suspense": actual_bank = found_bank

    cols = {c.lower(): c for c in df.columns}
    date_col = next((cols[k] for k in ['date', 'txn date'] if k in cols), None)
    desc_col = next((cols[k] for k in ['narration', 'description'] if k in cols), None)
    debit_col = next((cols[k] for k in ['debit', 'withdrawal'] if k in cols), None)
    credit_col = next((cols[k] for k in ['credit', 'deposit'] if k in cols), None)

    for _, row in df.iterrows():
        try:
            debit = float(str(row.get(debit_col, 0)).replace(',', '')) if row.get(debit_col) else 0
            credit = float(str(row.get(credit_col, 0)).replace(',', '')) if row.get(credit_col) else 0
            nar_raw = str(row.get(desc_col, ''))
            
            if debit > 0:
                vch_type, amt = "Payment", debit
                led1, led1_pos, led1_amt = (party_led_sel, "Yes", -amt)
                led2, led2_pos, led2_amt = (actual_bank, "No", amt)
            elif credit > 0:
                vch_type, amt = "Receipt", credit
                led1, led1_pos, led1_amt = (actual_bank, "Yes", -amt)
                led2, led2_pos, led2_amt = (party_led_sel, "No", amt)
            else: continue

            if "⭐" in party_led_sel and master_list:
                traced = trace_ledger(nar_raw, master_list)
                if vch_type == "Payment": led1 = traced
                else: led2 = traced

            # Strict XML Formatting matching 'good one.xml'
            try: date_str = pd.to_datetime(row.get(date_col)).strftime("%Y%m%d")
            except: date_str = "20260101"
            clean_nar = nar_raw.replace("&", "&amp;").replace("<", "&lt;")

            xml_body += f"""<TALLYMESSAGE xmlns:UDF="TallyUDF">
                <VOUCHER VCHTYPE="{vch_type}" ACTION="Create" OBJVIEW="Accounting Voucher View">
                <DATE>{date_str}</DATE><NARRATION>{clean_nar}</NARRATION><VOUCHERTYPENAME>{vch_type}</VOUCHERTYPENAME>
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
    
    # THE DYNAMIC FIX: Options only appear if synced
    synced_masters = []
    ledger_options = ["Please upload Master.html"] 
    
    if master_file:
        synced_masters = extract_ledger_names(master_file)
        st.success(f"✅ Synced {len(synced_masters)} ledgers")
        ledger_options = ["⭐ AI Auto-Trace (Premium)"] + synced_masters
    
    # No hardcoded SBI here anymore!
    bank_led = st.selectbox("Select Bank Ledger", ledger_options)
    party_led = st.selectbox("Select Default Party", ledger_options)

with col2:
    st.markdown("### 📂 2. Upload & Convert")
    bank_file = st.file_uploader("Drop Statement here (Excel or PDF)", type=['xlsx', 'xls', 'pdf'])
    if bank_file:
        if st.button("🚀 Convert to Tally XML"):
            df = load_data(bank_file)
            if df is not None:
                xml_data = generate_tally_xml(df, bank_led, party_led, synced_masters)
                st.balloons()
                st.success("Premium AI Match Complete!")
                st.download_button("⬇️ Download Tally XML File", xml_data, "tally_import.xml", use_container_width=True)

# --- 5. BRANDED FOOTER ---
s_logo = get_img_as_base64("logo 1.png")
s_html = f'<img src="data:image/png;base64,{s_logo}" width="25" style="vertical-align:middle; margin-right:5px;">' if s_logo else ""
st.markdown(f"""<div class="footer">
    <p>Sponsored By {s_html} <span class="brand-link" style="color:#0F172A;">Uday Mondal</span> | Consultant Advocate</p>
    <p style="font-size: 13px;">Powered & Created by <span class="brand-link">Debasish Biswas</span></p>
</div>""", unsafe_allow_html=True)
