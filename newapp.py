import streamlit as st
import pandas as pd
from bs4 import BeautifulSoup

# --- 1. Engine Logic ---
def extract_masters(html_file):
    soup = BeautifulSoup(html_file, 'html.parser')
    # Extracting names - adjust 'td' if your Tally HTML uses different tags
    return [td.text.strip() for td in soup.find_all('td') if len(td.text.strip()) > 1]

# --- 2. UI Integration ---
st.title("Accounting Expert | AI Bank")

# Column layout like in your screenshot
col1, col2 = st.columns(2)

with col1:
    st.markdown("### 🛠️ 1. Settings & Mapping")
    master_file = st.file_uploader("Upload Tally Master (Optional)", type="html")
    
    # Initialize variables
    master_ledgers = []
    default_options = ["31 Group(s) and 542 Ledger(s)"] # Your current default
    
    if master_file:
        master_ledgers = extract_masters(master_file)
        st.success(f"✅ Synced {len(master_ledgers)} ledgers")
        
        # PREPEND THE PREMIUM OPTION
        # This puts the Golden Star option at the very top of the list
        premium_option = "⭐ AI Auto-Trace (Match from Master)"
        display_options = [premium_option] + master_ledgers
        
        st.selectbox("Select Bank Ledger", ["State Bank of India -38500202509"])
        
        # THE UPDATED SELECT BOX
        selected_party = st.selectbox(
            "Select Default Party", 
            options=display_options,
            help="The ⭐ option will automatically find the right ledger for each entry!"
        )
        
        if selected_party == premium_option:
            st.toast("Premium Engine Enabled!", icon="⭐")
    else:
        # Fallback for standard users
        st.selectbox("Select Bank Ledger", ["State Bank of India -38500202509"])
        st.selectbox("Select Default Party", options=default_options)

with col2:
    st.markdown("### 📂 2. Upload & Convert")
    # ... your existing Bank Format and File Uploader code ...
