import streamlit as st
import pandas as pd
from bs4 import BeautifulSoup
import io

# --- 1. PRO ENGINE: MASTER LEDGER EXTRACTION ---

def get_ledger_names(html_file):
    """
    Parses Tally's master.html.
    Extracts ledger names typically found in <td> tags.
    """
    try:
        soup = BeautifulSoup(html_file, 'html.parser')
        # Filter out very short strings or empty cells
        ledgers = [td.text.strip() for td in soup.find_all('td') if len(td.text.strip()) > 1]
        return sorted(list(set(ledgers)))
    except Exception as e:
        st.error(f"Error reading master: {e}")
        return []

def auto_trace_logic(remark, master_list):
    """
    The 'AI' matching engine that looks for ledger names 
    inside bank statement narrations.
    """
    if pd.isna(remark) or not str(remark).strip():
        return "Suspense Ledger"
    
    remark_upper = str(remark).upper()
    for ledger in master_list:
        if ledger.upper() in remark_upper:
            return ledger
    return "Suspense Ledger"

# --- 2. THE UI LAYOUT ---

def main():
    st.set_page_config(page_title="Accounting Expert | AI Bank", layout="wide")
    
    st.markdown("# 🚀 Accounting Expert | AI Bank")
    st.markdown("---")

    # Initialize Sidebar or State-based variables
    if 'synced_ledgers' not in st.session_state:
        st.session_state.synced_ledgers = []

    # Two Column Layout (Mirroring your screenshot)
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 🛠️ 1. Settings & Mapping")
        
        # A. The Master Uploader
        master_file = st.file_uploader("Upload Tally Master (Optional)", type="html")
        
        # Default options before any sync
        party_options = ["31 Group(s) and 542 Ledger(s)"]
        is_premium = False

        if master_file:
            # Extract names and update session state
            st.session_state.synced_ledgers = get_ledger_names(master_file)
            st.success(f"✅ Synced {len(st.session_state.synced_ledgers)} ledgers")
            
            # --- THE GOLDEN STAR UPGRADE ---
            # We put the AI Auto-Trace option at the very top
            premium_label = "⭐ AI Auto-Trace (Premium)"
            party_options = [premium_label] + st.session_state.synced_ledgers
            is_premium = True

        # B. Bank Ledger Selection
        st.selectbox("Select Bank Ledger", ["State Bank of India -38500202509"])

        # C. The Dynamic "Select Default Party"
        # This box now reacts instantly to the file upload
        selected_party = st.selectbox(
            "Select Default Party", 
            options=party_options,
            index=0,
            help="Upload master.html to unlock ⭐ AI Tracking"
        )

        if is_premium and "⭐" in selected_party:
            st.toast("Pro Engine Active: AI Matching enabled!", icon="⭐")

    with col2:
        st.markdown("### 📂 2. Upload & Convert")
        
        bank_format = st.selectbox("Select Bank Format", ["SBI", "HDFC", "ICICI", "Other"])
        pdf_pass = st.text_input("PDF Password", type="password", placeholder="Optional")
        
        bank_file = st.file_uploader("Drop your Statement here (Excel or PDF)", type=["xlsx", "xls", "pdf"])

    # --- 3. THE PROCESSING ENGINE ---

    if bank_file:
        # Load bank data
        try:
            df = pd.read_excel(bank_file) if not bank_file.name.endswith('.pdf') else pd.DataFrame()
            
            if not df.empty:
                st.markdown("---")
                st.subheader("Data Preview & Premium Mapping")

                # If the user selected the Golden Star option
                if is_premium and "⭐" in selected_party:
                    # Identify narration column
                    cols = [c for c in df.columns if c.lower() in ['description', 'narration', 'particulars', 'remarks']]
                    desc_col = cols[0] if cols else None
                    
                    if desc_col:
                        st.info(f"AI is tracing ledgers from the '{desc_col}' column.")
                        # RUN THE MATCHING ENGINE
                        df['2nd_Ledger'] = df[desc_col].apply(lambda x: auto_trace_logic(x, st.session_state.synced_ledgers))
                    else:
                        st.warning("Could not find a narration column to match.")
                        df['2nd_Ledger'] = "Suspense Ledger"
                else:
                    # Standard manual mode
                    df['2nd_Ledger'] = selected_party

                st.dataframe(df)

                if st.button("Generate Tally XML"):
                    st.success("Tally XML Ready for Download!")
                    # (Insert your specific XML export code here)
        except Exception as e:
            st.error(f"Error processing bank statement: {e}")

if __name__ == "__main__":
    main()
