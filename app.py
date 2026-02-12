import streamlit as st
import pandas as pd
from bs4 import BeautifulSoup
import pdfplumber
import io
import base64

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(page_title="Accounting Expert | AI Bank to Tally", page_icon="logo.png", layout="wide")

# --- 2. FUTURISTIC THEME CSS ---
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
        html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #F8FAFC; color: #0F172A; }
        .hero-container { text-align: center; padding: 40px; background: linear-gradient(135deg, #065F46 0%, #1E40AF 100%); color: white; margin: -6rem -4rem 30px -4rem; }
        .stButton>button { width: 100%; background: linear-gradient(90deg, #10B981 0%, #3B82F6 100%); color: white; border-radius: 8px; height: 50px; font-weight: 600; border: none; }
        .footer { margin-top: 60px; padding: 30px; text-align: center; color: #64748B; border-top: 1px solid #E2E8F0; background-color: white; margin-left: -4rem; margin-right: -4rem; }
        #MainMenu, footer, header { visibility: hidden; }
    </style>
""", unsafe_allow_html=True)

# --- 3. CORE ENGINE FUNCTIONS ---

def extract_ledger_names(html_file):
    try:
        soup = BeautifulSoup(html_file, 'html.parser')
        return sorted(list(set([td.text.strip() for td in soup.find_all('td') if len(td.text.strip()) > 1])))
    except: return []

def trace_ledger_prioritized(remark, master_list, upi_sale_led, upi_pur_led, vch_type):
    if not remark or pd.isna(remark): return "Suspense"
    remark_up = str(remark).upper()
    for ledger in master_list:
        if ledger.upper() in remark_up: return ledger
    if "UPI" in remark_up:
        return upi_pur_led if vch_type == "Payment" else upi_sale_led
    return "Suspense"

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
    except Exception as e:
        st.error(f"Loader Error: {e}")
        return None

def generate_tally_xml(df, bank_led, party_led, master_list, upi_sale, upi_pur):
    """FIXED: Strictly adheres to 'good one.xml' tag structure and signs."""
    xml_header = """<ENVELOPE><HEADER><TALLYREQUEST>Import Data</TALLYREQUEST></HEADER><BODY><IMPORTDATA><REQUESTDESC><REPORTNAME>Vouchers</REPORTNAME></REQUESTDESC><REQUESTDATA>"""
    xml_footer = """</REQUESTDATA></IMPORTDATA></BODY></ENVELOPE>"""
    xml_body = ""
    
    cols = {str(c).lower().strip(): c for c in df.columns}
    d_col = next((cols[k] for k in ['tran date', 'date', 'txn date'] if k in cols), df.columns[0])
    n_col = next((cols[k] for k in ['narration', 'description'] if k in cols), df.columns[1])
    dr_col = next((cols[k] for k in ['withdrawal(dr)', 'debit', 'withdrawal'] if k in cols), None)
    cr_col = next((cols[k] for k in ['deposit(cr)', 'credit', 'deposit'] if k in cols), None)

    for _, row in df.iterrows():
        try:
            val_dr = float(str(row.get(dr_col, 0)).replace(',', '')) if dr_col and row.get(dr_col) else 0
            val_cr = float(str(row.get(cr_col, 0)).replace(',', '')) if cr_col and row.get(cr_col) else 0
            nar = str(row.get(n_col, ''))
            if val_dr <= 0 and val_cr <= 0: continue

            # VOUCHER SIGNAGE LOGIC
            if val_dr > 0:
                vch, amt = "Payment", val_dr
                l1_name, l1_pos, l1_amt = (party_led, "Yes", -amt)
                l2_name, l2_pos, l2_amt = (bank_led, "No", amt)
            else:
                vch, amt = "Receipt", val_cr
                l1_name, l1_pos, l1_amt = (bank_led, "Yes", -amt)
                l2_name, l2_pos, l2_amt = (party_led, "No", amt)

            # PRIORITY TRACING
            if "⭐" in party_led:
                traced = trace_ledger_prioritized(nar, master_list, upi_sale, upi_pur, vch)
                if vch == "Payment": l1_name = traced
                else: l2_name = traced

            clean_nar = nar.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            try: dt = pd.to_datetime(row.get(d_col)).strftime("%Y%m%d")
            except: dt = "20260101"

            xml_body += f"""<TALLYMESSAGE xmlns:UDF="TallyUDF">
                <VOUCHER VCHTYPE="{vch}" ACTION="Create" OBJVIEW="Accounting Voucher View">
                    <DATE>{dt}</DATE><NARRATION>{clean_nar}</NARRATION><VOUCHERTYPENAME>{vch}</VOUCHERTYPENAME>
                    <ALLLEDGERENTRIES.LIST><LEDGERNAME>{l1_name}</LEDGERNAME><ISDEEMEDPOSITIVE>{l1_pos}</ISDEEMEDPOSITIVE><AMOUNT>{l1_amt}</AMOUNT></ALLLEDGERENTRIES.LIST>
                    <ALLLEDGERENTRIES.LIST><LEDGERNAME>{l2_name}</LEDGERNAME><ISDEEMEDPOSITIVE>{l2_pos}</ISDEEMEDPOSITIVE><AMOUNT>{l2_amt}</AMOUNT></ALLLEDGERENTRIES.LIST>
                </VOUCHER></TALLYMESSAGE>"""
        except: continue
    return xml_header + xml_body + xml_footer

# --- 4. UI SECTIONS ---
st.markdown('<div class="hero-container"><h1>Accounting Expert</h1></div>', unsafe_allow_html=True)
c1, c2 = st.columns([1, 1.5], gap="large")

with c1:
    st.markdown("### 🛠️ 1. Settings")
    master = st.file_uploader("Upload Tally Master", type=['html'])
    synced, options = [], ["Upload Master.html first"]
    if master:
        synced = extract_ledger_names(master)
        st.success(f"✅ Synced {len(synced)} ledgers")
        options = ["⭐ AI Auto-Trace (Premium)"] + synced
    bank_led = st.selectbox("Select Bank Ledger", options)
    party_led = st.selectbox("Default Party", options)
    st.markdown("---")
    upi_sale = st.selectbox("UPI Receipts Ledger", options)
    upi_pur = st.selectbox("UPI Payments Ledger", options)

with c2:
    st.markdown("### 📂 2. Convert")
    bank_file = st.file_uploader("Drop Statement here", type=['xlsx', 'xls', 'pdf'])
    if bank_file:
        df = load_data(bank_file)
        if df is not None:
            st.dataframe(df.head(3), use_container_width=True)
            if st.button("🚀 Convert to Tally XML"):
                xml_data = generate_tally_xml(df, bank_led, party_led, synced, upi_sale, upi_pur)
                st.success("XML Generated!")
                st.download_button("⬇️ Download XML", xml_data, "tally_import.xml", use_container_width=True)

st.markdown("""<div class="footer"><p>Sponsored By <b>Uday Mondal</b> | Advocate</p><p style="font-size:12px;">Created by Debasish Biswas</p></div>""", unsafe_allow_html=True)
