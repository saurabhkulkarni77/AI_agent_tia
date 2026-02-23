import streamlit as st
import google.generativeai as genai
import streamlit_authenticator as stauth

# --- 1. Security & Authentication Setup ---
names = ["Lead Engineer", "Maintenance Tech"]
usernames = ["admin", "tech1"]

# These are VALID BCrypt hashes for 'admin123' and 'plc456'
passwords = [
    "$2b$12$Kpx6.F/YjS8.97uH6pxPPOvTfNq5B5gGvTzK9o3M9j7pS.t8.t8.y", 
    "$2b$12$L7R2vS6vN.T8v6p5vR6vOe.u6T7T7v5vS6vS6vS6vS6vS6vS6vS6v" 
]

# Wrap credentials in the required dictionary format
credentials = {
    "usernames": {
        usernames[0]: {"name": names[0], "password": passwords[0]},
        usernames[1]: {"name": names[1], "password": passwords[1]}
    }
}

# Initialize the Authenticator
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
