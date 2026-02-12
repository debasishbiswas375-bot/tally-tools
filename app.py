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
        .hero-container { text-align: center; padding: 40px; background: linear-gradient(135deg, #065F46 0%, #1E40AF 100%); color: white; margin: -6rem -4rem 30px -4rem; box-shadow: 0 10px 30px -10px rgba(6, 95, 70, 0.5); }
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

def trace_ledger_prioritized(remark, master_list):
    """
    Priority 1: Direct Match from Tally Masters
    Priority 2: UPI Method (Categorize as Sale/Purchase)
    Priority 3: Default to Suspense
    """
    if not remark or pd.isna(remark): return "Suspense"
    
    remark_up = str(remark).upper()

    # --- PRIORITY 1: SEARCH FOR SYNCED PARTY NAMES ---
    for ledger in master_list:
        if ledger.upper() in remark_up:
            return ledger

    # --- PRIORITY 2: UPI CATEGORIZATION (SECOND PRIORITY) ---
    if "UPI" in remark_up:
        if any(x in remark_up for x in ["PAYME", "SENT", "DR"]):
            return "UPI Purchase A/c" 
        if any(x in remark_up for x in ["CR", "RECEIVED", "BY"]):
            return "UPI Sale A/c"
    
    return "Suspense"

def load_data(file):
    """Cleans metadata and duplicate columns from bank files."""
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

        # 1. FIND REAL HEADER ROW
        header_idx = 0
        for i, row in df.iterrows():
            row_str = " ".join([str(x).lower() for x in row if x])
            if 'date' in row_str and ('narration' in row_str or 'description' in row_str):
                header_idx = i
                break
        
        # 2. RECONSTRUCT DF
        df.columns = [str(c).strip().upper() if not pd.isna(c) else f"COL_{j}" for j, c in enumerate(df.iloc[header_idx])]
        df = df[header_idx + 1:].reset_index(drop=True)
        
        # 3. FIX DUPLICATE COLUMNS
        cols = pd.Series(df.columns)
        for dup in cols[cols.duplicated()].unique():
            cols[cols[cols == dup].index.values.tolist()] = [f"{dup}_{k}" if k != 0 else dup for k in range(sum(cols == dup))]
        df.columns = cols
        
        return df.dropna(subset=[df.columns[1]], thresh=1)
    except Exception as e:
        st.error(f"Loader Error: {e}")
        return None

def generate_tally_xml(df, bank_led, party_led, master_list, is_preview=False):
    """Generates XML with signage from 'good one.xml'."""
    xml_header = """<ENVELOPE><HEADER><TALLYREQUEST>Import Data</TALLYREQUEST></HEADER><BODY><IMPORTDATA><REQUESTDESC><REPORTNAME>Vouchers</REPORTNAME></REQUESTDESC><REQUESTDATA>"""
    xml_footer = """</REQUESTDATA></IMPORTDATA></BODY></ENVELOPE>"""
    xml_body = ""
    
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
                l1, l1p, l1a = (party_led, "Yes", -amt), (bank_led, "No", amt)
            elif val_cr > 0:
                vch, amt = "Receipt", val_cr
                l1, l1p, l1a = (bank_led, "Yes", -amt), (party_led, "No", amt)
            else: continue

            if "⭐" in party_led:
                traced = trace_ledger_prioritized(nar, master_list)
                if vch == "Payment": l1 = (traced, "Yes", -amt)
                else: l1 = (l1[0], "Yes", -amt); l2 = (traced, "No", amt)
            else: l2 = (l1[1], l1[2], l1[3]) if 'l2' not in locals() else l2 # Helper for logic flow

            # Re-assigning l1 and l2 correctly for the XML block
            p_led, p_pos, p_amt = l1[0] if isinstance(l1, tuple) else l1, l1[1], l1[2]
            b_led, b_pos, b_amt = l2[0] if isinstance(l2, tuple) else l2, l2[1], l2[2]

            clean_nar = nar.replace("&", "&amp;").replace("<", "&lt;")
            try: dt = pd.to_datetime(row.get(d_col)).strftime("%Y%m%d")
            except: dt = "20260101"

            xml_body += f"""<TALLYMESSAGE xmlns:UDF="TallyUDF"><VOUCHER VCHTYPE="{vch}" ACTION="Create" OBJVIEW="Accounting Voucher View"><DATE>{dt}</DATE><NARRATION>{clean_nar}</NARRATION><VOUCHERTYPENAME>{vch}</VOUCHERTYPENAME><ALLLEDGERENTRIES.LIST><LEDGERNAME>{p_led}</LEDGERNAME><ISDEEMEDPOSITIVE>{p_pos}</ISDEEMEDPOSITIVE><AMOUNT>{p_amt}</AMOUNT></ALLLEDGERENTRIES.LIST><ALLLEDGERENTRIES.LIST><LEDGERNAME>{b_led}</LEDGERNAME><ISDEEMEDPOSITIVE>{b_pos}</ISDEEMEDPOSITIVE><AMOUNT>{b_amt}</AMOUNT></ALLLEDGERENTRIES.LIST></VOUCHER></TALLYMESSAGE>"""
        except: continue
    return xml_body if is_preview else xml_header + xml_body + xml_footer

# --- 4. UI SECTIONS ---
st.markdown('<div class="hero-container"><h1>Accounting Expert</h1><p>Premium AI Tally Automation</p></div>', unsafe_allow_html=True)

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
                # --- LIVE PREVIEW ---
                st.markdown("📋 **Live Accounting Match Preview**")
                n_c = next((c for c in df.columns if 'narration' in str(c).lower()), df.columns[1])
                preview = [{"Narration": str(row[n_c])[:60], "Matched Ledger": trace_ledger_prioritized(row[n_c], synced)} for _, row in df.head(5).iterrows()]
                st.table(preview)

                xml_data = generate_tally_xml(df, bank_led, party_led, synced)
                st.success("Premium AI Match Complete!")
                st.download_button("⬇️ Download XML", xml_data, "tally_import.xml", use_container_width=True)

# --- 5. FOOTER ---
st.markdown("""<div class="footer"><p>Sponsored By <b>Uday Mondal</b> | Advocate</p><p style="font-size:12px;">Created by Debasish Biswas</p></div>""", unsafe_allow_html=True)
