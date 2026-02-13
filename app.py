import streamlit as st
import pandas as pd
import re

# --- 1. PAGE CONFIG ---
st.set_page_config(
    page_title="Accounting Expert", 
    page_icon="logo.png",
    layout="wide",
    initial_sidebar_state="collapsed" 
)

# --- 2. THE UI ENGINE (CSS) ---
st.markdown("""
    <style>
        .main .block-container { padding-top: 6.5rem !important; }
        header, .stDeployButton, footer { visibility: hidden !important; display: none !important; }
        
        /* Hamburger Menu */
        [data-testid="stSidebarCollapsedControl"] {
            background-color: #10B981 !important;
            border-radius: 8px !important;
            width: 46px !important; height: 46px !important;
            top: 12px !important; left: 12px !important;
            display: flex !important; align-items: center; justify-content: center !important;
            z-index: 1000000 !important;
        }
        [data-testid="stSidebarCollapsedControl"] svg { display: none !important; }
        [data-testid="stSidebarCollapsedControl"]::before {
            content: ""; width: 22px; height: 2px; background: white;
            position: absolute; box-shadow: 0 7px 0 white, 0 -7px 0 white;
        }

        /* Hero & Sidebar */
        .hero-container {
            text-align: center; padding: 50px 20px;
            background: linear-gradient(135deg, #065F46 0%, #1E40AF 100%);
            color: white; margin: -7rem -4rem 30px -4rem;
            border-bottom: 5px solid #10B981;
        }
        [data-testid="stSidebar"] { background-color: #0F172A !important; border-right: 3px solid #10B981 !important; }
        [data-testid="stSidebar"] * { color: white !important; }
    </style>
""", unsafe_allow_html=True)

# --- 3. TOP NAVIGATION ---
st.markdown(f"""
    <div style="position: fixed; top: 12px; right: 12px; z-index: 1000000; display: flex; align-items: center; background: white; padding: 5px 15px; border-radius: 30px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
        <span style="color: #0F172A; margin-right:8px; font-weight:700;">Debasish</span>
        <img src="https://www.w3schools.com/howto/img_avatar.png" style="width: 35px; border-radius: 50%; border: 2px solid #10B981;">
    </div>
    """, unsafe_allow_html=True)

# --- 4. SIDEBAR ---
with st.sidebar:
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.image("https://www.w3schools.com/howto/img_avatar.png", width=90) 
    st.markdown('<h2 style="color: #10B981;">Accounting Expert</h2>', unsafe_allow_html=True)
    with st.expander("👤 Account", expanded=True):
        st.write("Debasish | Pro Tier")
    st.divider()

# --- 5. CORE LOGIC (The "Core Things") ---
def clean_currency(value):
    """Cleans currency strings into floats."""
    if pd.isna(value) or value == '': return 0.0
    val = re.sub(r'[^\d.]', '', str(value))
    try: return float(val)
    except: return 0.0

def smart_normalize(df):
    """Detects headers and maps columns to Tally standards."""
    if df is None or df.empty: return pd.DataFrame()
    df = df.dropna(how='all', axis=0).reset_index(drop=True)
    header_idx = None
    for i, row in df.iterrows():
        clean_row = [str(v).lower().strip() for v in row.values if v is not None]
        if 'date' in " ".join(clean_row):
            header_idx = i
            break
    if header_idx is not None:
        df.columns = df.iloc[header_idx]
        df = df[header_idx + 1:].reset_index(drop=True)
    df.columns = df.columns.astype(str).str.strip().str.lower()
    
    new_df = pd.DataFrame()
    col_map = {'Date':['date','txn'],'Narration':['narration','particular'],'Debit':['debit','dr'],'Credit':['credit','cr']}
    for target, aliases in col_map.items():
        found = next((c for c in df.columns if any(a in c for a in aliases)), None)
        new_df[target] = df[found] if found else (0.0 if target in ['Debit', 'Credit'] else "")
    return new_df

# --- 6. MAIN CONTENT ---
st.markdown('<div class="hero-container"><h1>Accounting Expert</h1><p>Core XML Engine Active</p></div>', unsafe_allow_html=True)

col1, col2 = st.columns(2, gap="large")
with col1:
    st.subheader("🛠️ Step 1")
    with st.container(border=True):
        master = st.file_uploader("Upload Tally Master", type=['html'])
        bank_led = st.selectbox("Bank Ledger", ["Suspense A/c", "HDFC Bank"])

with col2:
    st.subheader("📂 Step 2")
    with st.container(border=True):
        stmt = st.file_uploader("Upload Statement", type=['xlsx', 'pdf'])
        if stmt:
            # Running the core normalization logic
            df_raw = pd.read_excel(stmt) if stmt.name.endswith('xlsx') else None
            if df_raw is not None:
                df_clean = smart_normalize(df_raw)
                st.success("Core Engine: Data Normalized!")
                st.dataframe(df_clean.head(3)) # Preview of the core work
            
            if st.button("🚀 GENERATE XML"):
                st.download_button("⬇️ Download", "XML_CONTENT_HERE", "tally.xml")

st.markdown("<br><hr><center>tallytools.in</center>", unsafe_allow_html=True)
