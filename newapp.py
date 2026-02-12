import streamlit as st
import pandas as pd
from bs4 import BeautifulSoup

# --- 1. PREMIUM ENGINE: LEDGER EXTRACTION ---
def get_ledger_names(html_file):
    try:
        soup = BeautifulSoup(html_file, 'html.parser')
        # Extracts names from table data cells found in Tally Master HTML
        ledgers = [td.text.strip() for td in soup.find_all('td') if len(td.text.strip()) > 1]
        return sorted(list(set(ledgers)))
    except Exception:
        return []

# --- 2. MAIN APP LAYOUT ---
def main():
    st.set_page_config(page_title="Accounting Expert | AI Bank", layout="wide", page_icon="🛡️")

    # Banner / Header
    st.image("logo.png", width=100) # Ensure logo.png is in your GitHub
    st.title("Accounting Expert | AI Bank")
    st.markdown("---")

    # Sidebar: Admin/Premium Toggle
    # For now, we set this to True so you see the Premium features immediately
    is_premium = st.sidebar.toggle("Admin / Premium Mode", value=True)

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🛠️ 1. Settings & Mapping")
        
        master_file = st.file_uploader("Upload Tally Master (Optional)", type="html")
        
        # Logic to update the Dropdown
        party_options = ["31 Group(s)and542 Ledger(s)"]
        
        if master_file and is_premium:
            real_ledgers = get_ledger_names(master_file)
            st.success(f"✅ Synced {len(real_ledgers)} ledgers")
            
            # PREPEND THE GOLDEN STAR OPTION
            premium_label = "⭐ AI Auto-Trace (Premium)"
            party_options = [premium_label] + real_ledgers
        
        st.selectbox("Select Bank Ledger", ["State Bank of India -38500202509"])

        # This is the box you wanted to update
        selected_party = st.selectbox(
            "Select Default Party",
            options=party_options,
            index=0
        )

        if "⭐" in selected_party:
            st.toast("Premium Engine Active!", icon="⭐")

    with col2:
        st.subheader("📂 2. Upload & Convert")
        st.selectbox("Select Bank Format", ["SBI", "HDFC", "ICICI"])
        st.text_input("PDF Password", type="password")
        bank_file = st.file_uploader("Drop your Statement here", type=["xlsx", "xls", "pdf"])

    # --- 3. THE PROCESSING LOGIC ---
    if bank_file:
        st.info("Processing Bank Statement...")
        # Your conversion logic (from tally.py) would go here

if __name__ == "__main__":
    main()
