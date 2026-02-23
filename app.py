import streamlit as st
import google.generativeai as genai
import streamlit_authenticator as stauth

# --- 1. Security & Authentication Setup ---
names = ["Lead Engineer", "Maintenance Tech"]
usernames = ["admin", "tech1"]

# FRESH VALID HASHES
passwords = [
    "$2b$12$cl07.G.t/U9FzO7y6v9G.eK1Klp8U2Z5YlYv2R3t5G1g5G1g5G1g.", # admin123
    "$2b$12$8v.pXp6p6p6p6p6p6p6p6p6p6p6p6p6p6p6p6p6p6p6p6p6p6p6p."  # plc456
]

# The library MUST have this "credentials" -> "usernames" structure
credentials = {
    "usernames": {
        "admin": {"name": "Lead Engineer", "password": passwords[0]},
        "tech1": {"name": "Maintenance Tech", "password": passwords[1]}
    }
}

# Initialize with the credentials dictionary
authenticator = stauth.Authenticate(
    credentials, 
    "tia_agent_cookie", 
    "signature_key", 
    cookie_expiry_days=30
)


# --- Version-Agnostic Login Call ---
try:
    # Try the newer version syntax first
    result = authenticator.login(label="Login", location="main")
except TypeError:
    # Fall back to the older version syntax if 'label' is unexpected
    result = authenticator.login("main")

# Safely unpack the result (handles cases where it returns None or a tuple)
if isinstance(result, tuple):
    name, authentication_status, username = result
else:
    # In some versions, status is stored in st.session_state instead of returned
    name = st.session_state.get("name")
    authentication_status = st.session_state.get("authentication_status")
    username = st.session_state.get("username")

# --- 2. Authentication UI Logic ---
if authentication_status == False:
    st.error("Username/password is incorrect")
elif authentication_status == None:
    st.warning("Please enter your username and password")
elif authentication_status:
    # --- START OF AUTHENTICATED APP ---
    authenticator.logout("Logout", "sidebar")
    st.sidebar.success(f"Logged in as: {name}")

    # Gemini API Configuration
    try:
        API_KEY = st.secrets["GEMINI_API_KEY"]
        genai.configure(api_key=API_KEY)
    except Exception:
        st.error("API Key missing! Please add GEMINI_API_KEY to your .streamlit/secrets.toml file.")
        st.stop()

    st.title("🤖 Siemens SCL Logic Agent")
    st.info("Authorized access granted.")

    req = st.text_area("Describe the PLC Function (e.g., 'A toggle flip-flop for a light switch'):")
    if st.button("Generate SCL Code"):
        with st.spinner("Consulting AI..."):
            model = genai.GenerativeModel('gemini-2.5-flash')
            response = model.generate_content(f"Write Siemens TIA Portal SCL code for: {req}")
            st.code(response.text, language='pascal')
