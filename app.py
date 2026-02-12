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

def trace_ledger_priority(narration, master_list, upi_sale, upi_pur, vch_type):
    """Priority: 1. Masters | 2. UPI Backup | 3. Suspense."""
    if not narration or pd.isna(narration): return "Suspense"
    nar_up = str(narration).upper()
    # 1. Check Masters first
    for ledger in master_list:
        if ledger.upper() in nar_up: return ledger
    # 2. UPI Fallback
    if "UPI" in nar_up:
        return upi_pur if vch_type == "Payment" else upi_sale
    return "Suspense"

def load_data(file):
    """Robust loader for Excel/PDF."""
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
        
        # Header locator
        header_idx = 0
        for i, row in df.iterrows():
            row_str = " ".join([str(x).lower() for x in row if x])
            if 'date' in row_str and ('narration' in row_str or 'description' in row_str):
                header_idx = i
                break
        
        df.columns = [str(c).strip().upper() if not pd.isna(c) else f"COL_{j}" for j, c in enumerate(df.iloc[header_idx])]
        df = df[header_idx + 1:].reset_index(drop=True)
        
        # Resolve duplicates
        cols = pd.Series(df.columns)
        for dup in cols[cols.duplicated()].unique():
            cols[cols[cols == dup].index.values.tolist()] = [f"{dup}_{k}" if k != 0 else dup for k in range(sum(cols == dup))]
        df.columns = cols
        return df.dropna(subset=[df.columns[1]], thresh=1)
    except: return None

def generate_tally_xml(df, bank_led, synced, upi_sale, upi_pur):
    """XML generation following 'good one.xml' logic."""
    xml_header = """<ENVELOPE><HEADER><TALLYREQUEST>Import Data</TALLYREQUEST></HEADER><BODY><IMPORTDATA><REQUESTDESC><REPORTNAME>Vouchers</REPORTNAME></REQUESTDESC><REQUESTDATA>"""
    xml_footer = """</REQUESTDATA></IMPORTDATA></BODY></ENVELOPE>"""
    xml_body = ""
    
    # Column mapping
    cols = {str(c).lower(): c for c in df.columns}
    d_col = next((cols[k] for k in ['tran date', 'date'] if k in cols), df.columns[0])
    n_col = next((cols[k] for k in ['narration', 'description'] if k in cols), df.columns[1])
    dr_col = next((cols[k] for k in ['withdrawal(dr)', 'debit'] if k in cols), None)
    cr_col = next((cols[k] for k in ['deposit(cr)', 'credit'] if k in cols), None)

    for _, row in df.iterrows():
        try:
            dr = float(str(row.get(dr_col, 0)).replace(',', '')) if dr_col else 0
            cr = float(str(row.get(cr_col, 0)).replace(',', '')) if cr_col else 0
            nar = str(row.get(n_col, ''))
            
            if dr > 0:
                vch, amt = "Payment", dr
                target = trace_ledger_priority(nar, synced, upi_sale, upi_pur, vch)
                l1_n, l1_p, l1_a = target, "Yes", -amt
                l2_n, l2_p, l2_a = bank_led, "No", amt
            elif cr > 0:
                vch, amt = "Receipt", cr
                target = trace_ledger_priority(nar, synced, upi_sale, upi_pur, vch)
                l1_n, l1_p, l1_a = bank_led, "Yes", -amt
                l2_n, l2_p, l2_a = target, "No", amt
            else: continue

            xml_body += f"""<TALLYMESSAGE xmlns:UDF="TallyUDF"><VOUCHER VCHTYPE="{vch}" ACTION="Create"><DATE>{pd.to_datetime(row.get(d_col)).strftime('%Y%m%d')}</DATE><NARRATION>{nar.replace('&', '&amp;')}</NARRATION><VOUCHERTYPENAME>{vch}</VOUCHERTYPENAME><ALLLEDGERENTRIES.LIST><LEDGERNAME>{l1_n}</LEDGERNAME><ISDEEMEDPOSITIVE>{l1_p}</ISDEEMEDPOSITIVE><AMOUNT>{l1_a}</AMOUNT></ALLLEDGERENTRIES.LIST><ALLLEDGERENTRIES.LIST><LEDGERNAME>{l2_n}</LEDGERNAME><ISDEEMEDPOSITIVE>{l2_p}</ISDEEMEDPOSITIVE><AMOUNT>{l2_a}</AMOUNT></ALLLEDGERENTRIES.LIST></VOUCHER></TALLYMESSAGE>"""
        except: continue
    return xml_header + xml_body + xml_footer

# --- 4. UI ---
st.markdown('<div class="hero-container"><h1>Accounting Expert</h1></div>', unsafe_allow_html=True)
c1, c2 = st.columns([1, 1.5], gap="large")

with c1:
    st.markdown("### 🛠️ 1. Settings")
    master = st.file_uploader("Upload Tally Master", type=['html'])
    synced, options = [], ["Upload Master.html first"]
    if master:
        synced = extract_ledger_names(master)
        st.success(f"✅ Synced {len(synced)} ledgers")
        options = ["⭐ AI Auto-Trace"] + synced
    bank_led = st.selectbox("Select Bank", options)
    upi_sale = st.selectbox("UPI Sale Ledger", options)
    upi_pur = st.selectbox("UPI Purchase Ledger", options)

with c2:
    st.markdown("### 📂 2. Convert")
    bank_file = st.file_uploader("Drop Statement here", type=['xlsx', 'xls', 'pdf'])
    if bank_file:
        df = load_data(bank_file)
        if df is not None:
            st.dataframe(df.head(3), use_container_width=True)
            if st.button("🚀 Convert to Tally XML"):
                # PREVIEW TABLE
                st.markdown("### 📋 Accounting Preview")
                preview_list = []
                n_c = next((c for c in df.columns if 'NARRATION' in str(c)), df.columns[1])
                for _, r in df.head(10).iterrows():
                    vch = "Payment" if float(str(r.get(next((c for c in df.columns if 'WITHDRAWAL' in str(c)), df.columns[0]), 0)).replace(',', '')) > 0 else "Receipt"
                    preview_list.append({"Narration": str(r[n_c])[:50], "Target Ledger": trace_ledger_priority(r[n_c], synced, upi_sale, upi_pur, vch)})
                st.table(preview_list)
                
                xml_data = generate_tally_xml(df, bank_led, synced, upi_sale, upi_pur)
                st.success("XML Ready!")
                st.download_button("⬇️ Download XML", xml_data, "tally_import.xml")

st.markdown(f"""<div class="footer"><p>Sponsored By <b>Uday Mondal</b> | Advocate</p><p style="font-size:12px;">Created by Debasish Biswas</p></div>""", unsafe_allow_html=True)
