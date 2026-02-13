import streamlit as st

# Page Config
st.set_page_config(page_title="Accounting Tools", layout="wide")

# Custom CSS to match the website's styling
st.markdown("""
    <style>
    /* Main Background and Colors */
    .main {
        background-color: #ffffff;
    }
    
    /* Hero Section */
    .hero-container {
        background: linear-gradient(180deg, #005f73 0%, #0a9396 100%);
        padding: 100px 20px;
        text-align: center;
        color: white;
        border-radius: 0 0 50% 50% / 20px;
    }
    
    .hero-title {
        font-family: 'serif';
        font-size: 3rem;
        font-weight: bold;
        margin-bottom: 10px;
    }
    
    .hero-subtitle {
        font-size: 1.2rem;
        opacity: 0.9;
        margin-bottom: 30px;
    }

    /* Buttons */
    .stButton>button {
        background-color: white;
        color: #005f73;
        border-radius: 5px;
        padding: 10px 25px;
        font-weight: bold;
        border: none;
    }

    /* Section Headers */
    .section-header {
        color: #003d4d;
        text-align: center;
        font-family: 'serif';
        margin-top: 50px;
    }
    </style>
    """, unsafe_allow_stdio=True)

# --- HERO SECTION ---
st.markdown(f"""
    <div class="hero-container">
        <h1 class="hero-title">Learn Tally & Accounting for Free</h1>
        <p class="hero-subtitle">Perfect for Accountants, Bookkeepers, and Small Businesses in India.</p>
    </div>
    """, unsafe_allow_html=True)

# Center the button under the hero (Streamlit columns for centering)
col1, col2, col3 = st.columns([2, 1, 2])
with col2:
    if st.button("📊 View Tool Outline"):
        st.write("Redirecting...")

st.markdown("---")

# --- TRUST LOGOS (Placeholder) ---
st.markdown("<p style='text-align:center; color:grey; font-size:0.8rem;'>AS SEEN ON</p>", unsafe_allow_html=True)
l_col1, l_col2, l_col3, l_col4 = st.columns(4)
l_col1.image("https://via.placeholder.com/100x30?text=TallyPrime", use_container_width=False)
l_col2.image("https://via.placeholder.com/100x30?text=GST+India", use_container_width=False)
l_col3.image("https://via.placeholder.com/100x30?text=MSME", use_container_width=False)
l_col4.image("https://via.placeholder.com/100x30?text=Excel", use_container_width=False)

# --- TOPICS SECTION ---
st.markdown("<h2 class="section-header">Choose a Tool to Get Started</h2>", unsafe_allow_html=True)

t_col1, t_col2 = st.columns(2)

with t_col1:
    st.info("### 01. Excel to Tally XML")
    st.write("Convert your bank statements and sales data instantly.")
    if st.button("Start Converting", key="tool1"):
        pass

with t_col2:
    st.success("### 02. Ledger Management")
    st.write("Clean up and organize your Tally ledgers efficiently.")
    if st.button("Open Ledger Tool", key="tool2"):
        pass
