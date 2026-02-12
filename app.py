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
        .stButton>button { width: 100%; background: linear-gradient(90deg, #10B981 0%, #3B82F6 100%); color: white; border-radius: 8px; height: 55px; font-weight: 600; border: none; box-shadow: 0 4px 15px rgba(16, 185, 129, 0.3); }
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
        ledgers = [td.text.strip() for td in soup.find_all('td') if len(td.text.strip()) > 1]
        return sorted(list(set(ledgers)))
    except: return []

def trace_ledger(text, master_list):
    """Fuzzy matching: returns ledger if found in text, else 'Suspense'."""
    if not text or pd.isna(text): return "Suspense"
    text_up = str(text).upper()
    for ledger in master_list:
        if ledger.upper() in text_up: return ledger
    return "Suspense"

def load_data(file):
    """Detects headers dynamically to ensure data collection."""
    try:
        if file.name.lower().endswith('.pdf'):
            all_rows = []
            with pdfplumber.open(file) as pdf:
                for page in pdf.pages:
                    table = page.extract_table()
                    if table: all_rows.extend(table)
            df = pd.DataFrame(all_rows)
        else:
            df = pd.read_excel(file)
        
        # --- IMPROVED HEADER FINDER ---
        for i, row in df.iterrows():
            row_str = " ".join([str(x).lower() for x in row if x])
            if 'date' in row_str and ('narration' in row_str or 'description' in row_str or 'particulars' in row_str):
                df.columns = df.iloc[i]
                return df[i+1:].reset_index(drop=True)
        return df # Fallback to raw data if no header found
    except Exception as e:
        st.error(f"Error reading file: {e}")
        return None

def generate_tally_xml(df, bank_led_sel, party_led_sel, master_list):
    """Produces exact structure of 'good one.xml'."""
    xml_header = """<ENVELOPE><HEADER><TALLYREQUEST>Import Data</TALLYREQUEST></HEADER><BODY><IMPORTDATA><REQUESTDESC><REPORTNAME>Vouchers</REPORTNAME></REQUESTDESC><REQUESTDATA>"""
    xml_footer = """</REQUESTDATA></IMPORTDATA></BODY></ENVELOPE>"""
    xml_body = ""
    
    # Identify dynamic columns
    cols = {str(c).lower().strip(): c for c in df.columns if c}
    date_col = next((cols[k] for k in ['date', 'txn date', 'transaction date'] if k in cols), df.columns[0])
    desc_col = next((cols[k] for k in ['narration', 'description', 'particulars'] if k in cols), df.columns[1])
    debit_col = next((cols[k] for k in ['debit', 'withdrawal', 'dr'] if k in cols), None)
    credit_col = next((cols[k] for k in ['credit', 'deposit', 'cr'] if k in cols), None)

    for _, row in df.iterrows():
        try:
            # Logic from verified 'good one.xml'
            val_dr = float(str(row.get(debit_col, 0)).replace(',', '')) if debit_col and row.get(debit_col) else 0
            val_cr = float(str(row.get(credit_col, 0)).replace(',', '')) if credit_col and row.get(credit_col) else 0
            nar_raw = str(row.get(desc_col, ''))
            
            if val_dr > 0:
                vch_type, amt = "Payment", val_dr
                led1, led1_pos, led1_amt = (party_led_sel, "Yes", -amt)
                led2, led2_pos, led2_amt = (bank_led_sel, "No", amt)
            elif val_cr > 0:
                vch_type, amt = "Receipt", val_cr
                led1, led1_pos, led1_amt = (bank_led_sel, "Yes", -amt)
                led2, led2_pos, led2_amt = (party_led_sel, "No", amt)
            else: continue

            # AI Auto-Trace logic
            if "⭐" in party_led_sel and master_list:
                traced = trace_ledger(nar_raw, master_list)
                if vch_type == "Payment": led1 = traced
                else: led2 = traced

            # Character cleaning for Tally
            clean_nar = nar_raw.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            try: d_str = pd.to_datetime(row.get(date_col)).strftime("%Y%m%d")
            except: d_str = "20260101"

            xml_body += f"""<TALLYMESSAGE xmlns:UDF="TallyUDF"><VOUCHER VCHTYPE="{vch_type}" ACTION="Create" OBJVIEW="Accounting Voucher View"><DATE>{d_str}</DATE><NARRATION>{clean_nar}</NARRATION><VOUCHERTYPENAME>{vch_type}</VOUCHERTYPENAME><ALLLEDGERENTRIES.LIST><LEDGERNAME>{led1}</LEDGERNAME><ISDEEMEDPOSITIVE>{led1_pos}</ISDEEMEDPOSITIVE><AMOUNT>{led1_amt}</AMOUNT></ALLLEDGERENTRIES.LIST><ALLLEDGERENTRIES.LIST><LEDGERNAME>{led2}</LEDGERNAME><ISDEEMEDPOSITIVE>{led2_pos}</ISDEEMEDPOSITIVE><AMOUNT>{led2_amt}</AMOUNT></ALLLEDGERENTRIES.LIST></VOUCHER></TALLYMESSAGE>"""
        except: continue
    return xml_header + xml_body + xml_footer

# --- 4. UI DASHBOARD ---

hero_logo = get_img_as_base64("logo.png")
hero_html = f'<img src="data:image/png;base64,{hero_logo}" width="120">' if hero_logo else ""
st.markdown(f'<div class="hero-container">{hero_html}<div style="font-size:3.5rem; font-weight:800;">Accounting Expert</div></div>', unsafe_allow_html=True)

c1, c2 = st.columns([1, 1.5], gap="large")

with c1:
    st.markdown("### 🛠️ 1. Settings & Mapping")
    master_file = st.file_uploader("Upload Tally Master (Optional)", type=['html'])
    synced_masters, ledger_options = [], ["Upload Master.html first"]
    if master_file:
        synced_masters = extract_ledger_names(master_file)
        st.success(f"✅ Synced {len(synced_masters)} ledgers")
        ledger_options = ["⭐ AI Auto-Trace (Premium)"] + synced_masters
    bank_led = st.selectbox("Select Bank Ledger", ["State Bank of India -38500202509"] + synced_masters)
    party_led = st.selectbox("Select Default Party", ledger_options)

with c2:
    st.markdown("### 📂 2. Upload & Convert")
    bank_file = st.file_uploader("Drop Statement here (Excel or PDF)", type=['xlsx', 'xls', 'pdf'])
    if bank_file:
        df = load_data(bank_file)
        if df is not None:
            st.markdown("##### 🔍 Data Preview")
            st.dataframe(df.head(5), use_container_width=True) # Show raw data to confirm it's reading
            
            if st.button("🚀 Convert to Tally XML"):
                xml_data = generate_tally_xml(df, bank_led, party_led, synced_masters)
                st.balloons()
                st.success("Premium AI Match Complete!")
                st.download_button("⬇️ Download Tally XML File", xml_data, "tally_import.xml", use_container_width=True)

# --- 5. BRANDED FOOTER ---
s_logo = get_img_as_base64("logo 1.png")
s_html = f'<img src="data:image/png;base64,{s_logo}" width="25" style="vertical-align:middle; margin-right:5px;">' if s_logo else ""
st.markdown(f"""<div class="footer"><p>Sponsored By {s_html} <span class="brand-link" style="color:#0F172A;">Uday Mondal</span> | Consultant Advocate</p><p style="font-size: 13px;">Powered & Created by <span class="brand-link">Debasish Biswas</span></p></div>""", unsafe_allow_html=True)
