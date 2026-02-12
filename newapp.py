import streamlit as st
import pandas as pd
from bs4 import BeautifulSoup
import io

# --- 1. THE PRO ENGINE: LEDGER TRACKING ---

def extract_ledgers_from_html(html_file):
    """
    Parses Tally's master.html to extract ledger names.
    Tally exports usually wrap names in <td> or <span> tags.
    """
    try:
        soup = BeautifulSoup(html_file, 'html.parser')
        # Extracts text from table cells, filtering out empty or short strings
        ledgers = [td.text.strip() for td in soup.find_all('td') if len(td.text.strip()) > 1]
        return sorted(list(set(ledgers)))
    except Exception as e:
        st.error(f"Error parsing master.html: {e}")
        return []

def auto_match_ledger(remark, master_list):
    """
    Logic to find a ledger name within a bank remark/description.
    """
    if pd.isna(remark) or not str(remark).strip():
        return "Suspense Ledger"
    
    remark_upper = str(remark).upper()
    for ledger in master_list:
        if ledger.upper() in remark_upper:
            return ledger
    return "Suspense Ledger"

# --- 2. THE UI AND WORKFLOW ---

def main():
    st.set_page_config(page_title="Accounting Expert Pro", layout="wide")
    
    st.title("📊 Accounting Expert: Excel to Tally")
    st.subheader("Major Update: Smart Auto-Ledger Tracking")

    # --- Sidebar: User Management & Plan Logic ---
    st.sidebar.header("User Control")
    
    # Placeholder for your Supabase login logic
    # For now, we use a session state to simulate a Pro User login
    if 'is_pro' not in st.session_state:
        st.session_state.is_pro = False

    # Simulate login check
    user_status = "Pro" if st.session_state.is_pro else "Standard"
    st.sidebar.info(f"Current Plan: {user_status}")

    if not st.session_state.is_pro:
        if st.sidebar.button("Demo: Unlock Pro Features"):
            st.session_state.is_pro = True
            st.rerun()

    # --- Main App Logic ---
    
    # 1. Upload Bank Statement (Available to all)
    bank_file = st.file_uploader("Upload Bank Statement (Excel)", type=["xlsx", "xls"])
    
    master_ledgers = []
    
    # 2. Upload Master.html (Pro Feature Only)
    if st.session_state.is_pro:
        st.markdown("---")
        st.markdown("### 🚀 Pro Feature: Auto-Trace Ledgers")
        master_file = st.file_uploader("Upload Tally master.html to sync your ledgers", type="html")
        
        if master_file:
            master_ledgers = extract_ledgers_from_html(master_file)
            st.success(f"Successfully synced {len(master_ledgers)} ledgers from your Tally Master.")
    else:
        st.warning("🔒 Upload 'master.html' to enable auto-ledger tracking (Pro Only).")

    # 3. Processing the Data
    if bank_file:
        df = pd.read_excel(bank_file)
        
        # Identify the description column (customize these names based on your template)
        desc_col = next((col for col in df.columns if col.lower() in ['description', 'narration', 'remarks']), None)
        
        if desc_col and master_ledgers:
            st.write("### Processing with Auto-Tracking...")
            # Create the 2nd ledger column based on the master list
            df['Target_Ledger'] = df[desc_col].apply(lambda x: auto_match_ledger(x, master_ledgers))
        else:
            # Fallback for standard users or missing columns
            df['Target_Ledger'] = "Suspense Ledger"

        st.dataframe(df)

        # 4. XML Generation (Placeholder for your existing tally.py logic)
        if st.button("Generate Tally XML"):
            # Insert your XML generation logic here
            st.success("XML Generated successfully!")
            # st.download_button("Download XML", data=xml_data, file_name="tally_import.xml")

if __name__ == "__main__":
    main()
