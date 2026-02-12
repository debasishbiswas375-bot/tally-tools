import streamlit as st
import pandas as pd
from bs4 import BeautifulSoup
import pdfplumber
import io
import base64
import re

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Accounting Expert | AI Bank to Tally",
    page_icon="logo.png",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 2. IMAGE HANDLER (Prevents Crash) ---
def get_img_as_base64(file):
    try:
        with open(file, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except: return None

# --- 3. FUTURISTIC TALLY THEME CSS (Original Design) ---
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
        html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #F8FAFC; }
        
        .hero-container { 
            text-align: center; padding: 50px 20px; 
            background: linear-gradient(135deg, #065F46 0%, #1E40AF 100%); 
            color: white; margin: -6rem -4rem 30px -4rem; 
        }
        
        .bank-detect-box { 
            background-color: #E0F2FE; border: 1px solid #3B82F6; 
            padding: 15px; border-radius: 12px; color: #1E3A8A; 
            font-weight: 700; margin-bottom: 20px; text-align: center; border-left: 8px solid #3B82F6; 
        }
        
        .warning-box { 
            background-color: #FEF2F2; border: 1px solid #EF4444; 
            padding: 15px; border-radius: 10px; margin: 15px 0; 
            color: #991B1B; font-weight: 600; border-left: 8px solid #EF4444; 
        }
        
        .stButton>button { 
            width: 100%; background: #10B981; color: white; 
            height: 55px; font-weight: 600; border-radius: 12px; 
            border: none; box-shadow: 0 4px 15px rgba(16, 185, 129, 0.3); 
        }
        
        .footer { 
            position: fixed; left: 0; bottom: 0; width: 100%; 
            background-color: white; color: #64748B; text-align: center; 
            padding: 12px 0; border-top: 1px solid #E2E8F0; z-index: 1000; font-size: 0.9rem; 
        }
        
        .main-content { padding-bottom: 120px; }
        #MainMenu, footer, header { visibility: hidden; }
    </style>
""", unsafe_allow_html=True)

# --- 4. CORE ENGINES (Optimized for Speed) ---

def extract_ledger_names(html_file):
    try:
        soup = BeautifulSoup(html_file, 'html.parser')
        return sorted(list(set([td.text.strip() for td in soup.find_all('td') if len(td.text.strip()) > 1])))
    except: return []

def trace_identity_power(narration, master_list):
    """Matches longest name first to separate Mithu Sk vs Mondal."""
    if not narration or pd.isna(narration): return "Suspense", "None"
    nar_up = str(narration).upper()
    # Sort masters by length for precision
    sorted_masters = sorted(master_list, key=len, reverse=True)
    for ledger in sorted_masters:
        if re.search(rf"\b{re.escape(ledger.upper())}\b", nar_up):
            return ledger, "🎯 Direct Match"
    if "UPI" in nar_up: return "Untraced", "⚠️ UPI Alert"
    return "Suspense", "None"

def generate_tally_xml(df, bank_led, synced, upi_fix_led=None):
    """Engine to create the actual importable file."""
    xml_start = '<?xml version="1.0"?><ENVELOPE><HEADER><TALLYREQUEST>Import Data</TALLYREQUEST></HEADER><BODY><IMPORTDATA><REQUESTDESC><REPORTNAME>Vouchers</REPORTNAME></REQUESTDESC><REQUESTDATA>'
    xml_end = '</REQUESTDATA></IMPORTDATA></BODY></ENVELOPE>'
    xml_body = ""
    
    n_c = next((c for c in df.columns if any(k in str(c) for k in ['NARRATION', 'DESC'])), df.columns[1])
    dr_c = next((c for c in df.columns if any(k in str(c) for k in ['WITHDRAWAL', 'DEBIT'])), None)
    cr_c = next((c for c in df.columns if any(k in str(c) for k in ['DEPOSIT', 'CREDIT'])), None)
    d_c = next((c for c in df.columns if 'DATE' in str(c)), df.columns[0])

    for _, row in df.iterrows():
        try:
            nar = str(row[n_c]).replace('&', '&amp;')
            dt = pd.to_datetime(row[d_c]).strftime('%Y%m%d')
            val_dr = float(str(row.get(dr_c, 0)).replace(',', '')) if dr_c and row[dr_c] else 0
            val_cr = float(str(row.get(cr_c, 0)).replace(',', '')) if cr_c and row[cr_c] else 0
            
            target, status = trace_identity_power(nar, synced)
            if status == "⚠️ UPI Alert" and upi_fix_led: target = upi_fix_led
            
            if val_dr > 0:
                vch, amt = "Payment", val_dr
                xml_body += f"<TALLYMESSAGE><VOUCHER VCHTYPE='{vch}'><DATE>{dt}</DATE><NARRATION>{nar}</NARRATION><ALLLEDGERENTRIES.LIST><LEDGERNAME>{target}</LEDGERNAME><AMOUNT>-{amt}</AMOUNT></ALLLEDGERENTRIES.LIST><ALLLEDGERENTRIES.LIST><LEDGERNAME>{bank_led}</LEDGERNAME><AMOUNT>{amt}</AMOUNT></ALLLEDGERENTRIES.LIST></VOUCHER></TALLYMESSAGE>"
            elif val_cr > 0:
                vch, amt = "Receipt", val_cr
                xml_body += f"<TALLYMESSAGE><VOUCHER VCHTYPE='{vch}'><DATE>{dt}</DATE><NARRATION>{nar}</NARRATION><ALLLEDGERENTRIES.LIST><LEDGERNAME>{bank_led}</LEDGERNAME><AMOUNT>-{amt}</AMOUNT></ALLLEDGERENTRIES.LIST><ALLLEDGERENTRIES.LIST><LEDGERNAME>{target}</LEDGERNAME><AMOUNT>{amt}</AMOUNT></ALLLEDGERENTRIES.LIST></VOUCHER></TALLYMESSAGE>"
        except: continue
    return xml_start + xml_body + xml_end

def load_data(file):
    try:
        if file.name.lower().endswith('.pdf'):
            with pdfplumber.open(file) as pdf:
                all_data = [row for page in pdf.pages for row in (page.extract_table() or [])]
            df = pd.DataFrame(all_data)
        else:
            df = pd.read_excel(file, header=None)
        
        for i, row in df.iterrows():
            row_str = " ".join([str(x).lower() for x in row if x])
            if 'narration' in row_str and 'date' in row_str:
                df.columns = [str(c).strip().upper() for c in df.iloc[i]]
                return df[i+1:].reset_index(drop=True).dropna(subset=[df.columns[1]], thresh=1), df.iloc[:i]
        return None, None
    except: return None, None

# --- 5. UI IMPLEMENTATION ---
l_top = get_img_as_base64("logo.png")
l_top_html = f'<img src="data:image/png;base64,{l_top}" width="80" style="margin-bottom:10px;">' if l_top else ""
st.markdown(f'<div class="hero-container">{l_top_html}<h1>Accounting Expert</h1><p>BOB 0138 Identity Trace System</p></div>', unsafe_allow_html=True)

st.markdown('<div class="main-content">', unsafe_allow_html=True)
col1, col2 = st.columns([1, 1.5], gap="large")

with col1:
    st.markdown("### 🛠️ 1. Settings")
    master_file = st.file_uploader("Upload Master.html", type=['html'])
    synced = extract_ledger_names(master_file) if master_file else []
    if synced: st.toast(f"✅ {len(synced)} Ledgers Synced!")
    bank_ledger = st.selectbox("Select Bank Account", ["⭐ Auto-Detect"] + synced)

with col2:
    st.markdown("### 📂 2. Convert & Preview")
    bank_file = st.file_uploader("Upload BOB Statement", type=['xlsx', 'xls', 'pdf'])
    
    if bank_file and master_file:
        df, meta = load_data(bank_file)
        if df is not None:
            # Bank Detect
            active_bank = bank_ledger
            if bank_ledger == "⭐ Auto-Detect" and "0138" in str(meta.values).upper():
                active_bank = next((l for l in synced if "0138" in l), bank_ledger)
            
            st.markdown(f'<div class="bank-detect-box">🏦 Bank Account: <b>{active_bank}</b></div>', unsafe_allow_html=True)
            
            n_c = next((c for c in df.columns if any(k in str(c) for k in ['NARRATION', 'DESC'])), df.columns[1])
            unmatched = [idx for idx, r in df.iterrows() if trace_identity_power(r[n_c], synced)[1] == "⚠️ UPI Alert"]
            
            st.write("**Smart Identity Preview:**")
            st.table([{"Narration": str(row[n_c])[:50], "Target": trace_identity_power(row[n_c], synced)[0]} for _, row in df.head(5).iterrows()])

            # DOWNLOAD LOGIC
            if len(unmatched) > 5:
                st.markdown(f'<div class="warning-box">⚠️ Found {len(unmatched)} Untraced Items!</div>', unsafe_allow_html=True)
                upi_fix = st.selectbox("Assign Untraced to:", synced)
                if st.button("🚀 Process & Generate Tally XML"):
                    xml = generate_tally_xml(df, active_bank, synced, upi_fix)
                    st.balloons()
                    st.download_button("⬇️ Download tally_import.xml", xml, "tally_import.xml")
            else:
                if st.button("🚀 Convert to Tally XML"):
                    xml = generate_tally_xml(df, active_bank, synced)
                    st.balloons()
                    st.download_button("⬇️ Download tally_import.xml", xml, "tally_import.xml")

st.markdown('</div>', unsafe_allow_html=True)

# Footer
l_foot = get_img_as_base64("logo 1.png")
f_logo = f'<img src="data:image/png;base64,{l_foot}" width="25" style="vertical-align: middle; margin-right: 8px;">' if l_foot else ""
st.markdown(f'<div class="footer">{f_logo}Sponsored By <b>Uday Mondal</b> | Created by <b>Debasish Biswas</b></div>', unsafe_allow_html=True)
