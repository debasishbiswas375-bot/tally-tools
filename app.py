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
        .footer { margin-top: 60px; padding: 30px; text-align: center; color: #64748B; border-top: 1px solid #E2E8F0; background-color: white; margin-left: -4rem; margin-right: -4rem; }
        .brand-link { color: #059669; text-decoration: none; font-weight: 700; }
        .stButton>button { width: 100%; background: linear-gradient(90deg, #10B981 0%, #3B82F6 100%); color: white; border-radius: 8px; height: 50px; font-weight: 600; border: none; }
        #MainMenu, footer, header { visibility: hidden; }
    </style>
""", unsafe_allow_html=True)

# --- 3. CORE ENGINE FUNCTIONS ---

def extract_ledger_names(html_file):
    try:
        soup = BeautifulSoup(html_file, 'html.parser')
        return sorted(list(set([td.text.strip() for td in soup.find_all('td') if len(td.text.strip()) > 1])))
    except: return []

def trace_ledger(text, master_list):
    if not text or pd.isna(text): return "Suspense"
    text_up = str(text).upper()
    for ledger in master_list:
        if ledger.upper() in text_up: return ledger
    return "Suspense"

def load_data(file):
    """FIX: Aggressively cleans metadata and duplicate columns from bank files."""
    try:
        if file.name.lower().endswith('.pdf'):
            all_rows = []
            with pdfplumber.open(file) as pdf:
                for page in pdf.pages:
                    table = page.extract_table()
                    if table: all_rows.extend(table)
            df = pd.DataFrame(all_rows)
        else:
            # Load with no header initially to find the real table start
            df = pd.read_excel(file, header=None)

        # 1. FIND REAL HEADER ROW (e.g., row containing 'TRAN DATE')
        header_idx = 0
        for i, row in df.iterrows():
            row_str = " ".join([str(x).lower() for x in row if x])
            if 'tran date' in row_str or 'txn date' in row_str or 'narration' in row_str:
                header_idx = i
                break
        
        # 2. RECONSTRUCT DF FROM REAL START
        df.columns = [str(c).strip().upper() if not pd.isna(c) else f"COL_{j}" for j, c in enumerate(df.iloc[header_idx])]
        df = df[header_idx + 1:].reset_index(drop=True)
        
        # 3. FIX DUPLICATE COLUMNS (Fixes the ValueError)
        cols = pd.Series(df.columns)
        for dup in cols[cols.duplicated()].unique():
            cols[cols[cols == dup].index.values.tolist()] = [f"{dup}_{i}" if i != 0 else dup for i in range(sum(cols == dup))]
        df.columns = cols
        
        return df.dropna(subset=[df.columns[1]], thresh=1) # Remove empty decorative rows
    except Exception as e:
        st.error(f"Loader Error: {e}")
        return None

def generate_tally_xml(df, bank_led, party_led, master_list, is_preview=False):
    """Generates XML based on 'good one.xml' signage logic."""
    xml_header = """<ENVELOPE><HEADER><TALLYREQUEST>Import Data</TALLYREQUEST></HEADER><BODY><IMPORTDATA><REQUESTDESC><REPORTNAME>Vouchers</REPORTNAME></REQUESTDESC><REQUESTDATA>"""
    xml_footer = """</REQUESTDATA></IMPORTDATA></BODY></ENVELOPE>"""
    xml_body = ""
    
    # Identify standard columns even if names vary
    cols = {str(c).lower().strip(): c for c in df.columns}
    d_col = next((cols[k] for k in ['tran date', 'date', 'txn date'] if k in cols), df.columns[0])
    n_col = next((cols[k] for k in ['narration', 'description'] if k in cols), df.columns[1])
    dr_col = next((cols[k] for k in ['withdrawal(dr)', 'debit', 'withdrawal'] if k in cols), None)
    cr_col = next((cols[k] for k in ['deposit(cr)', 'credit', 'deposit'] if k in cols), None)

    rows = df.head(5) if is_preview else df
    for _, row in rows.iterrows():
        try:
            val_dr = float(str(row.get(dr_col, 0)).replace(',', '')) if dr_col and row.get(dr_col) else 0
            val_cr = float(str(row.get(cr_col, 0)).replace(',', '')) if cr_col and row.get(cr_col) else 0
            nar = str(row.get(n_col, ''))
            
            if val_dr > 0:
                vch, amt = "Payment", val_dr
                l1, l1p, l1a = (party_led, "Yes", -amt)
                l2, l2p, l2a = (bank_led, "No", amt)
            elif val_cr > 0:
                vch, amt = "Receipt", val_cr
                l1, l1p, l1a = (bank_led, "Yes", -amt)
                l2, l2p, l2a = (party_led, "No", amt)
            else: continue

            if "⭐" in party_led and master_list:
                traced = trace_ledger(nar, master_list)
                if vch == "Payment": l1 = traced
                else: l2 = traced

            clean_nar = nar.replace("&", "&amp;").replace("<", "&lt;")
            try: dt = pd.to_datetime(row.get(d_col)).strftime("%Y%m%d")
            except: dt = "20260101"

            xml_body += f"""<TALLYMESSAGE xmlns:UDF="TallyUDF"><VOUCHER VCHTYPE="{vch}" ACTION="Create" OBJVIEW="Accounting Voucher View"><DATE>{dt}</DATE><NARRATION>{clean_nar}</NARRATION><VOUCHERTYPENAME>{vch}</VOUCHERTYPENAME><ALLLEDGERENTRIES.LIST><LEDGERNAME>{l1}</LEDGERNAME><ISDEEMEDPOSITIVE>{l1p}</ISDEEMEDPOSITIVE><AMOUNT>{l1a}</AMOUNT></ALLLEDGERENTRIES.LIST><ALLLEDGERENTRIES.LIST><LEDGERNAME>{l2}</LEDGERNAME><ISDEEMEDPOSITIVE>{l2p}</ISDEEMEDPOSITIVE><AMOUNT>{l2a}</AMOUNT></ALLLEDGERENTRIES.LIST></VOUCHER></TALLYMESSAGE>"""
        except: continue
    return xml_body if is_preview else xml_header + xml_body + xml_footer

# --- 4. UI SECTIONS ---
hero_logo_b64 = base64.b64encode(open("logo.png", "rb").read()).decode() if io.open("logo.png", "rb") else ""
st.markdown(f'<div class="hero-container"><img src="data:image/png;base64,{hero_logo_b64}" width="100"><h1>Accounting Expert</h1></div>', unsafe_allow_html=True)

col1, col2 = st.columns([1, 1.5], gap="large")

with col1:
    st.markdown("### 🛠️ 1. Settings")
    master = st.file_uploader("Upload Tally Master", type=['html'])
    synced, options = [], ["Upload Master.html first"]
    if master:
        synced = extract_ledger_names(master)
        st.success(f"✅ Synced {len(synced)} ledgers")
        options = ["⭐ AI Auto-Trace (Premium)"] + synced
    bank_led = st.selectbox("Select Bank Ledger", options)
    party_led = st.selectbox("Default Party", options)

with col2:
    st.markdown("### 📂 2. Convert")
    bank_file = st.file_uploader("Drop Statement here", type=['xlsx', 'xls', 'pdf'])
    if bank_file:
        df = load_data(bank_file)
        if df is not None:
            st.dataframe(df.head(3), use_container_width=True)
            if st.button("🚀 Convert to Tally XML"):
                xml_data = generate_tally_xml(df, bank_led, party_led, synced)
                st.code(generate_tally_xml(df, bank_led, party_led, synced, True), language='xml')
                st.success("Premium AI Match Complete!")
                st.download_button("⬇️ Download XML", xml_data, "tally_import.xml", use_container_width=True)

# --- 5. FOOTER ---
st.markdown("""<div class="footer"><p>Sponsored By <span class="brand-link">Uday Mondal</span> | Consultant Advocate</p><p style="font-size:12px;">Created by <span class="brand-link">Debasish Biswas</span></p></div>""", unsafe_allow_html=True)
