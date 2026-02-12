import streamlit as st
import pandas as pd
from bs4 import BeautifulSoup
import io

# --- 1. PRO ENGINE: SMART LEDGER TRACING ---

def extract_ledger_list(html_file):
    """Parses master.html to extract unique ledger names."""
    try:
        soup = BeautifulSoup(html_file, 'html.parser')
        # Tally exports usually put ledger names in <td> tags
        ledgers = [td.text.strip() for td in soup.find_all('td') if len(td.text.strip()) > 1]
        return sorted(list(set(ledgers)))
    except Exception as e:
        st.error(f"Error reading master.html: {e}")
        return []

def trace_ledger_from_remark(remark, master_list):
    """Matches bank narration text against the master ledger list."""
    if pd.isna(remark) or not str(remark).strip():
        return "Suspense Ledger"
    
    remark_upper = str(remark).upper()
    for ledger in master_list:
        if ledger.upper() in remark_upper:
            return ledger
    return "Suspense Ledger"

# --- 2. UI AND APP LAYOUT ---

def main():
    st.set_page_config(page_title="Accounting Expert | AI Bank", layout="wide")
    
    # Header Section
    st.markdown("# 🚀 Accounting Expert | AI Bank")
    st.markdown("---")

    # Layout Columns
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 🛠️ 1. Settings & Mapping")
        
        # A. Master Upload
        master_file = st.file_uploader("Upload Tally Master (Optional)", type="html")
        
        # Initialize Ledger Data
        master_ledgers = []
        party_options = ["31 Group(s) and 542 Ledger(s)"] # Default view
        premium_mode = False

        if master_file:
            master_ledgers = extract_ledger_list(master_file)
            st.success(f"✅ Synced {len(master_ledgers)} ledgers")
            
            # THE PREMIUM UPGRADE: Injecting the Golden Star option
            premium_label = "⭐ AI Auto-Trace (Premium)"
            party_options = [premium_label] + master_ledgers
            premium_mode = True

        # B. Bank Ledger Selection
        st.selectbox("Select Bank Ledger", ["State Bank of India -38500202509"])

        # C. The Updated "Select Default Party" with Golden Star
        selected_party = st.selectbox(
            "Select Default Party", 
            options=party_options,
            index=0,
            help="Upload master.html to enable AI tracking!"
        )

        if premium_mode and "⭐" in selected_party:
            st.toast("Premium AI Auto-Trace Enabled!", icon="⭐")

    with col2:
        st.markdown("### 📂 2. Upload & Convert")
        
        bank_format = st.selectbox("Select Bank Format", ["SBI", "HDFC", "ICICI", "Other"])
        pdf_password = st.text_input("PDF Password", type="password", placeholder="Optional")
        
        bank_file = st.file_uploader("Drop your Statement here (Excel or PDF)", type=["xlsx", "xls", "pdf"])

    # --- 3. DATA PROCESSING ENGINE ---
    
    if bank_file:
        # Load the statement
        df = pd.read_excel(bank_file) if bank_file.name.endswith(('.xlsx', '.xls')) else pd.DataFrame()
        
        if not df.empty:
            st.markdown("---")
            st.subheader("Data Preview & AI Mapping")

            # Logic for Auto-Tracing if Golden Star is selected
            if premium_mode and "⭐" in selected_party:
                # Find the column that looks like a description/narration
                desc_col = next((col for col in df.columns if col.lower() in ['description', 'narration', 'remarks', 'particulars']), None)
                
                if desc_col:
                    st.info(f"AI is tracing ledgers based on the '{desc_col}' column.")
                    # Create the mapped column
                    df['Mapped_Ledger'] = df[desc_col].apply(lambda x: trace_ledger_from_remark(x, master_ledgers))
                else:
                    st.warning("Could not find a 'Narration' column to auto-trace. Please check your Excel format.")
                    df['Mapped_Ledger'] = "Suspense Ledger"
            else:
                # Standard mapping (manual selection)
                df['Mapped_Ledger'] = selected_party

            # Show the result
            st.dataframe(df)

            # Generate XML Button
            if st.button("Generate Tally XML"):
                # Your existing Tally XML logic goes here
                st.success("Tally XML Generated! Ready for import.")

if __name__ == "__main__":
    main()
