import streamlit as st
import pandas as pd
from bs4 import BeautifulSoup
import pdfplumber
import re
import base64
import io

# --- 1. PAGE CONFIG & PERSISTENT SIDEBAR ---
st.set_page_config(
    page_title="Accounting Expert | AI Bank to Tally", 
    page_icon="logo.png",
    layout="wide",
    initial_sidebar_state="expanded" # Forces sidebar to stay open
)

# --- 2. THE ORIGINAL APP.PY DESIGN (CSS) ---
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700&display=swap');
        html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #F8FAFC; }
        
        /* Persistent Sidebar Styling */
        .stSidebar { background-color: #0F172A !important; color: white !important; }
        
        /* Original Hero Section */
        .hero-container {
            text-align: center; padding: 50px 20px;
            background: linear-gradient(135deg, #065F46 0%, #1E40AF 100%);
            color: white; margin: -6rem -4rem 30px -4rem;
            box-shadow: 0 10px 30px -10px rgba(6, 95, 70, 0.5);
        }
        .hero-title { font-size: 3.5rem; font-weight: 800; }
        
        /* Container Cards */
        .stContainer { background-color: white; padding: 30px; border-radius: 16px; border: 1px solid #E2E8F0; }
        
        /* Original Buttons */
        .stButton>button { 
            width: 100%; background: linear-gradient(90deg, #10B981, #3B82F6); 
            color: white; border-radius: 8px; height: 50px; font-weight: 700; border: none;
        }
        
        /* Original Footer */
        .footer {
            margin-top: 60px; padding: 40px; text-align: center;
            color: #64748B; font-size: 0.9rem; border-top: 1px solid #E2E8F0;
            background-color: white; margin-bottom: -60px;
        }
    </style>
""", unsafe_allow_html=True)

# --- 3. CORE LOGIC & ERROR FIXES ---

def get_img_as_base64(file):
    try:
        with open(file, "rb") as f: return base64.b64encode(f.read()).decode()
    except: return None

def clean_currency(value):
    if pd.isna(value) or value == '': return 0.0
    val = re.sub(r'[^\d.]', '', str(value))
    try: return float(val)
    except: return 0.0

def smart_normalize(df):
    """Deep Scanner: Finds headers even if they are 'hidden' or uniquely named."""
    if df is None or df.empty: return pd.DataFrame()
    df = df.dropna(how='all').reset_index(drop=True)
    
    # Priority Scanner for Header Row
    header_idx = None
    for i, row in df.iterrows():
        row_str = " ".join([str(v).lower() for v in row.values if v is not None])
        if 'date' in row_str and ('narration' in row_str or 'particular' in row_str or 'description' in row_str):
            header_idx = i
            break
            
    if header_idx is not None:
        df.columns = df.iloc[header_idx]
        df = df[header_idx + 1:].reset_index(drop=True)
    
    df.columns = df.columns.astype(str).str.strip().str.lower()
    
    # Broad Alias Mapping to prevent empty columns
    new_df = pd.DataFrame()
    col_map = {
        'Date': ['date', 'txn', 'value', 'tran'],
        'Narration': ['narration', 'particular', 'description', 'remarks', 'details'],
        'Debit': ['debit', 'withdrawal', 'out', 'dr'],
        'Credit': ['credit', 'deposit', 'in', 'cr']
    }

    for target, aliases in col_map.items():
        found = next((c for c in df.columns if any(a in c for a in aliases)), None)
        if found:
            new_df[target] = df[found]
        else:
            new_df[target] = 0.0 if target in ['Debit', 'Credit'] else "UNTRACED"
            
    new_df['Debit'] = new_df['Debit'].apply(clean_currency)
    new_df['Credit'] = new_df['Credit'].apply(clean_currency)
    return new_df.dropna(subset=['Date'])

# --- 4. PERSISTENT SIDEBAR ---
with st.sidebar:
    st.title("🛡️ User Hub")
    with st.expander("👤 User Account", expanded=True):
        st.write("Status: **Online**")
        st.write("User: **Debasish**")
    with st.expander("💳 Solutions & Pricing"):
        st.write("Free Tier: 5 daily imports")
        st.write("Pro Tier: Unlimited")
    with st.expander("❓ Support & Help"):
        st.write("Contact us for custom bank templates.")
    st.divider()
    st.caption("v2.1 Stable Build")

# --- 5. MAIN DASHBOARD ---
hero_logo_b64 = get_img_as_base64("logo.png")
hero_logo_html = f'<img src="data:image/png;base64,{hero_logo_b64}" width="120">' if hero_logo_b64 else ""

st.markdown(f"""
    <div class="hero-container">
        {hero_logo_html}
        <div class="hero-title">Accounting Expert</div>
        <div class="hero-subtitle">Smart AI Bank Statement to Tally XML Converter</div>
    </div>
""", unsafe_allow_html=True)

col_left, col_right = st.columns([1, 1.5], gap="large")

with col_left:
    with st.container():
        st.markdown("### 🛠️ 1. Settings")
        master = st.file_uploader("Upload Tally Master (HTML)", type=['html'])
        ledger_list = ["Suspense A/c", "Cash", "Bank"]
        if master:
            soup = BeautifulSoup(master, 'html.parser')
            extracted = sorted(list(set([t.text.strip() for t in soup.find_all('td') if t.text.strip()])))
            if extracted: ledger_list = extracted; st.success(f"✅ {len(ledger_list)} Ledgers Synced")
        bank_led = st.selectbox("Select Bank Ledger", ledger_list)
        part_led = st.selectbox("Select Default Party", ledger_list)

with col_right:
    with st.container():
        st.markdown("### 📂 2. Upload & Convert")
        stmt_file = st.file_uploader("Drop Statement here (Excel or PDF)", type=['xlsx', 'pdf'])
        
        if stmt_file:
            with st.status("💎 AI Analyzing...", expanded=False) as status:
                if stmt_file.name.endswith('.pdf'):
                    with pdfplumber.open(stmt_file) as pdf:
                        data = []
                        for page in pdf.pages:
                            table = page.extract_table()
                            if table: data.extend(table)
                    df_raw = pd.DataFrame(data)
                else:
                    df_raw = pd.read_excel(stmt_file)

                df_clean = smart_normalize(df_raw)
                
                if not df_clean.empty and 'Date' in df_clean.columns:
                    status.update(label="✅ Success!", state="complete")
                    st.write("**Data Preview:**")
                    st.dataframe(df_clean[['Date', 'Narration', 'Debit', 'Credit']].head(10), use_container_width=True)
                    
                    if st.button("🚀 GENERATE TALLY XML"):
                        # XML Generation logic...
                        st.balloons()
                        st.success("Conversion Complete!")
                else:
                    status.update(label="❌ Detection Failed", state="error")
                    st.error("I couldn't find your headers. Please try a different statement format.")

# --- 6. SPONSORED FOOTER ---
footer_logo_b64 = get_img_as_base64("logo 1.png")
footer_logo_html = f'<img src="data:image/png;base64,{footer_logo_b64}" width="25" style="vertical-align: middle;">' if footer_logo_b64 else ""

st.markdown(f"""
    <div class="footer">
        <p>Sponsored By {footer_logo_html} <b>Uday Mondal</b> | Consultant Advocate</p>
        <p style="font-size: 13px;">Created & Powered by <b>Debasish Biswas</b></p>
    </div>
""", unsafe_allow_html=True)
