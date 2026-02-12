import streamlit as st
import pandas as pd
from bs4 import BeautifulSoup
import pdfplumber
import io
import base64
import re

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(page_title="Accounting Expert", layout="wide", initial_sidebar_state="collapsed")

# --- 2. HELPER: IMAGE TO BASE64 (With Error Handling) ---
def get_base64_image(img_path):
    try:
        with open(img_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except:
        return None

# --- 3. UI & PINNED SLIM FOOTER CSS ---
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
        html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #F8FAFC; }
        .hero-container { text-align: center; padding: 40px; background: linear-gradient(135deg, #065F46 0%, #1E40AF 100%); color: white; margin: -6rem -4rem 20px -4rem; }
        .bank-detect-box { background-color: #E0F2FE; border: 1px solid #3B82F6; padding: 12px; border-radius: 8px; color: #1E3A8A; font-weight: 700; margin-top: 10px; text-align: center; border-left: 8px solid #3B82F6; }
        .footer { position: fixed; left: 0; bottom: 0; width: 100%; background-color: white; color: #64748B; text-align: center; padding: 10px 0; border-top: 1px solid #E2E8F0; z-index: 1000; font-size: 0.85rem; }
        .main-content { padding-bottom: 110px; }
        #MainMenu, footer, header { visibility: hidden; }
    </style>
""", unsafe_allow_html=True)

# --- 4. CORE ENGINES ---

def extract_ledger_names(html_file):
    try:
        soup = BeautifulSoup(html_file, 'html.parser')
        return sorted(list(set([td.text.strip() for td in soup.find_all('td') if len(td.text.strip()) > 1])))
    except: return []

def trace_identity_power(narration, master_list):
    if not narration or pd.isna(narration): return "Suspense", "None"
    nar_up = str(narration).upper().replace('/', ' ')
    sorted_masters = sorted(master_list, key=len, reverse=True)
    for ledger in sorted_masters:
        pattern = rf"\b{re.escape(ledger.upper())}\b"
        if re.search(pattern, nar_up): return ledger, "🎯 Direct Match"
    if "UPI" in nar_up: return "Untraced", "⚠️ UPI Alert"
    return "Suspense", "None"

def generate_tally_xml(df, bank_led, synced, upi_fix_led=None):
    """Produces a Tally Prime compatible XML file."""
    xml_header = """<?xml version="1.0"?><ENVELOPE><HEADER><TALLYREQUEST>Import Data</TALLYREQUEST></HEADER><BODY><IMPORTDATA><REQUESTDESC><REPORTNAME>Vouchers</REPORTNAME></REQUESTDESC><REQUESTDATA>"""
    xml_footer = """</REQUESTDATA></IMPORTDATA></BODY></ENVELOPE>"""
    xml_body = ""
    
    # Fuzzy Column Finder
    n_c = next((c for c in df.columns if any(k in str(c) for k in ['NARRATION', 'DESC', 'PARTICULAR'])), df.columns[1])
    dr_c = next((c for c in df.columns if any(k in str(c) for k in ['WITHDRAWAL', 'DEBIT', 'DR'])), None)
    cr_c = next((c for c in df.columns if any(k in str(c) for k in ['DEPOSIT', 'CREDIT', 'CR'])), None)
    d_c = next((c for c in df.columns if 'DATE' in str(c)), df.columns[0])

    for _, row in df.iterrows():
        try:
            val_dr = float(str(row.get(dr_c, 0)).replace(',', '')) if dr_c and row.get(dr_c) else 0
            val_cr = float(str(row.get(cr_c, 0)).replace(',', '')) if cr_c and row.get(cr_c) else 0
            dt = pd.to_datetime(row.get(d_c)).strftime("%Y%m%d")
            target, status = trace_identity_power(row[n_c], synced)
            if status == "⚠️ UPI Alert" and upi_fix_led: target = upi_fix_led
            
            if val_dr > 0:
                l1_n, l1_p, l1_a, vch = target, "Yes", -val_dr, "Payment"
                l2_n, l2_p, l2_a = bank_led, "No", val_dr
            elif val_cr > 0:
                l1_n, l1_p, l1_a, vch = bank_led, "Yes", -val_cr, "Receipt"
                l2_n, l2_p, l2_a = target, "No", val_cr
            else: continue

            xml_body += f"""<TALLYMESSAGE xmlns:UDF="TallyUDF"><VOUCHER VCHTYPE="{vch}" ACTION="Create"><DATE>{dt}</DATE><NARRATION>{row[n_c]}</NARRATION><VOUCHERTYPENAME>{vch}</VOUCHERTYPENAME><ALLLEDGERENTRIES.LIST><LEDGERNAME>{l1_n}</LEDGERNAME><ISDEEMEDPOSITIVE>{l1_p}</ISDEEMEDPOSITIVE><AMOUNT>{l1_a}</AMOUNT></ALLLEDGERENTRIES.LIST><ALLLEDGERENTRIES.LIST><LEDGERNAME>{l2_n}</LEDGERNAME><ISDEEMEDPOSITIVE>{l2_p}</ISDEEMEDPOSITIVE><AMOUNT>{l2_a}</AMOUNT></ALLLEDGERENTRIES.LIST></VOUCHER></TALLYMESSAGE>"""
        except: continue
    return xml_header + xml_body + xml_footer

def load_data(file):
    try:
        if file.name.lower().endswith('.pdf'):
            with pdfplumber.open(file) as pdf:
                all_data = []
                for page in pdf.pages:
                    table = page.extract_table()
                    if table: all_data.extend(table)
            df = pd.DataFrame(all_data)
        else:
            df = pd.read_excel(file, header=None)
        
        for i, row in df.iterrows():
            row_str = " ".join([str(x).lower() for x in row if x])
            if 'narration' in row_str or 'date' in row_str:
                df.columns = [str(c).strip().upper() for c in df.iloc[i]]
                return df[i+1:].reset_index(drop=True).dropna(subset=[df.columns[1]], thresh=1), df.iloc[:i]
        return None, None
    except: return None, None

# --- 5. UI DASHBOARD ---
st.markdown('<div class="hero-container"><h1>Accounting Expert</h1></div>', unsafe_allow_html=True)
st.markdown('<div class="main-content">', unsafe_allow_html=True)

c1, c2 = st.columns([1, 1.5], gap="large")

with c1:
    st.markdown("### 🛠️ 1. Settings")
    master = st.file_uploader("Upload Tally Master", type=['html'])
    synced = []
    if master:
        synced = extract_ledger_names(master)
        st.toast(f"✅ {len(synced)} Ledgers Synced!")
    bank_choice = st.selectbox("Select Bank Account", ["⭐ Auto-Detect"] + synced)

with c2:
    st.markdown("### 📂 2. Convert & Preview")
    bank_file = st.file_uploader("Upload BOB Statement", type=['xlsx', 'xls', 'pdf'])
    if bank_file and master:
        df, meta = load_data(bank_file)
        if df is not None:
            active_bank = bank_choice
            if bank_choice == "⭐ Auto-Detect":
                full_meta = " ".join(meta.astype(str).values.flatten()).upper()
                if "0138" in full_meta:
                    active_bank = next((l for l in synced if "0138" in l), bank_choice)
            st.markdown(f'<div class="bank-detect-box">🏦 Bank Account: <b>{active_bank}</b></div>', unsafe_allow_html=True)
            
            n_c = next((c for c in df.columns if any(k in str(c) for k in ['NARRATION', 'DESC'])), df.columns[1])
            unmatched = [idx for idx, r in df.iterrows() if trace_identity_power(r[n_c], synced)[1] == "⚠️ UPI Alert"]
            
            st.table([{"Narration": str(row[n_c])[:50], "Target": trace_identity_power(row[n_c], synced)[0]} for _, row in df.head(5).iterrows()])

            if st.button("🚀 Convert to Tally XML"):
                st.balloons()
                xml = generate_tally_xml(df, active_bank, synced, upi_fix_led=None)
                st.download_button("⬇️ Download tally_import.xml", xml, file_name="tally_import.xml")

st.markdown('</div>', unsafe_allow_html=True)

# --- 6. PINNED SLIM FOOTER ---
l1 = get_base64_image("logo.png")
l2 = get_base64_image("logo 1.png")
l1_h = f'<img src="data:image/png;base64,{l1}" width="25" style="vertical-align:middle; margin-right:10px;">' if l1 else ""
l2_h = f'<img src="data:image/png;base64,{l2}" width="20" style="vertical-align:middle; margin-right:5px;">' if l2 else ""

st.markdown(f"""<div class="footer">{l1_h} Sponsored By {l2_h} <b>Uday Mondal</b> | Created by <b>Debasish Biswas</b></div>""", unsafe_allow_html=True)
