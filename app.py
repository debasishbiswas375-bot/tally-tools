import streamlit as st
import pandas as pd
from bs4 import BeautifulSoup
import pdfplumber
import re
import time

# --- 1. CYBER-PUNK UI THEME ---
st.set_page_config(page_title="Accounting Expert AI", layout="wide", page_icon="💎")

st.markdown("""
    <style>
        /* Cyber-dark background */
        .main { background-color: #0F172A; color: #E2E8F0; }
        .stSidebar { background-color: #1E293B !important; border-right: 1px solid #334155; }
        
        /* Glassmorphism Cards */
        div.stBlock {
            background: rgba(30, 41, 59, 0.7);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 20px;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }

        /* Futuristic Button */
        .stButton>button {
            width: 100%;
            background: linear-gradient(90deg, #10B981 0%, #3B82F6 100%);
            color: white;
            border: none;
            border-radius: 10px;
            height: 3.5rem;
            font-weight: 700;
            transition: 0.3s;
        }
        .stButton>button:hover { transform: scale(1.02); box-shadow: 0 0 15px #10B981; }
        
        /* Sidebar Text */
        .sidebar-text { color: #94A3B8; font-size: 0.85rem; }
    </style>
""", unsafe_allow_html=True)

# --- 2. THE PERSISTENT SIDEBAR (Login/Plans/Help) ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/6513/6513830.png", width=80)
    st.title("User Hub")
    
    # login/Account Section
    with st.expander("👤 User Account", expanded=True):
        st.write("Logged in as: **Guest**")
        if st.button("Logout"): pass
    
    # Plans Section
    with st.expander("💳 Subscription Plans"):
        st.markdown("""
        - **Basic:** 10 Imports/mo
        - **Expert:** Unlimited
        - **Custom:** API Access
        """)
        st.info("Your Plan: **Free Tier**")
    
    # Help & Support
    with st.expander("❓ Help & Solutions"):
        st.write("For 'Detection Failed' errors, ensure your PDF is not an image-based scan.")
        st.link_button("Get Live Support", "https://wa.me/yournumber")

    st.divider()
    st.markdown('<p class="sidebar-text">Powered by Debasish Biswas</p>', unsafe_allow_html=True)

# --- 3. PROCESSING LOGIC ---

def clean_currency(value):
    if pd.isna(value) or value == '': return 0.0
    val = re.sub(r'[^\d.]', '', str(value))
    try: return float(val)
    except: return 0.0

def smart_normalize(df):
    """Refined to find headers even in messy PDFs."""
    if df is None or df.empty: return pd.DataFrame()
    df = df.dropna(how='all').reset_index(drop=True)
    
    header_idx = None
    for i, row in df.iterrows():
        # Safely convert row to string to avoid AttributeErrors
        row_str = " ".join([str(val).lower() for val in row.values if val is not None])
        if 'date' in row_str and ('narration' in row_str or 'particular' in row_str):
            header_idx = i
            break
            
    if header_idx is not None:
        df.columns = df.iloc[header_idx]
        df = df[header_idx + 1:].reset_index(drop=True)
    
    df.columns = df.columns.astype(str).str.strip().str.lower()
    
    new_df = pd.DataFrame()
    # Broad mapping to catch different bank formats
    col_map = {
        'Date': ['date', 'txn', 'value'],
        'Narration': ['narration', 'particular', 'description', 'remarks'],
        'Debit': ['debit', 'withdrawal', 'out', 'dr'],
        'Credit': ['credit', 'deposit', 'in', 'cr']
    }

    for target, aliases in col_map.items():
        found = next((c for c in df.columns if any(a in c for a in aliases)), None)
        if found:
            new_df[target] = df[found]
        else:
            new_df[target] = 0.0 if target in ['Debit', 'Credit'] else "UNTRACED"
            
    return new_df

# --- 4. MAIN ENGINE ---
st.title("🚀 Accounting Expert AI Engine")

col_config, col_process = st.columns([1, 2], gap="large")

with col_config:
    st.subheader("1. Master Config")
    master = st.file_uploader("Upload Tally Master", type=['html'])
    ledgers = ["Suspense A/c"]
    if master:
        soup = BeautifulSoup(master, 'html.parser')
        ledgers = sorted(list(set([t.text.strip() for t in soup.find_all('td') if t.text.strip()])))
        st.success(f"✅ {len(ledgers)} Ledgers Synced")
    
    bank_led = st.selectbox("Bank Ledger", ledgers)
    part_led = st.selectbox("Default Party Ledger", ledgers)

with col_process:
    st.subheader("2. AI Analysis")
    stmt = st.file_uploader("Upload Bank Statement (PDF/Excel)", type=['pdf', 'xlsx'])
    
    if stmt:
        with st.status("💎 AI Analysis in Progress...", expanded=True) as status:
            st.write("🛠️ Initializing Neural Parsing...")
            time.sleep(1)
            
            if stmt.name.endswith('.pdf'):
                with pdfplumber.open(stmt) as pdf:
                    data = []
                    for page in pdf.pages:
                        table = page.extract_table()
                        if table: data.extend(table)
                df_raw = pd.DataFrame(data)
            else:
                df_raw = pd.read_excel(stmt)

            st.write("🧬 Finalizing Data Normalization...")
            df_clean = smart_normalize(df_raw)
            
            if not df_clean.empty and 'Date' in df_clean.columns:
                status.update(label="✅ Success: Data Mapped", state="complete", expanded=False)
                st.dataframe(df_clean.head(10), use_container_width=True)
                
                if st.button("GENERATE & DOWNLOAD TALLY XML"):
                    st.balloons()
                    # XML generation logic here...
            else:
                status.update(label="❌ Detection Failed", state="error")
                st.error("I couldn't detect the headers. Please check if the PDF is text-readable.")
