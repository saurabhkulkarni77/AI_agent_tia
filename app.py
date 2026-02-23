import streamlit as st
import google.generativeai as genai
import streamlit_authenticator as stauth

# --- 1. Security & Authentication Setup ---
names = ["Lead Engineer", "Maintenance Tech"]
usernames = ["admin", "tech1"]

# IMPORTANT: These must be valid BCrypt hashes. 
# You can generate them using: stauth.Hasher(['admin123']).generate()
# Hashed versions of 'admin123' and 'plc456'
passwords = [
    "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36RQoeG6L4zgn88WWf.baBK", 
    "$2b$12$8v.pXp6p6p6p6p6p6p6p6p6p6p6p6p6p6p6p6p6p6p6p6p6p6p6p."
] 

# The library expects the dictionary to be nested under "credentials"
credentials = {
    "usernames": {
        usernames[0]: {"name": names[0], "password": passwords[0]},
        usernames[1]: {"name": names[1], "password": passwords[1]}
    }
}

# Initialize the Authenticate object
authenticator = stauth.Authenticate(
    credentials, 
    "tia_agent_cookie", 
    "signature_key", 
    cookie_expiry_days=30
)

# FIX: In v0.2.x, login only takes the location ('main' or 'sidebar')
# It returns (name, authentication_status, username)
login_data = authenticator.login('main')

# Handle the tuple return safely
if login_data:
    name, authentication_status, username = login_data
else:
    # Fallback if the method returns None unexpectedly
    authentication_status = None

# --- 2. Authentication Logic ---
if authentication_status == False:
    st.error("Username/password is incorrect")
elif authentication_status == None:
    st.warning("Please enter your username and password")
elif authentication_status:
    # --- START OF AUTHENTICATED APP ---
    authenticator.logout("Logout", "sidebar")
    st.sidebar.title(f"Welcome {name}")

    # Secure API Config
    try:
        API_KEY = st.secrets["GEMINI_API_KEY"]
        genai.configure(api_key=API_KEY)
    except Exception:
        st.error("API Key missing in secrets!")
        st.stop()

    model = genai.GenerativeModel('gemini-2.5-flash')

    st.title("🤖 Secured Siemens SCL Agent")
    
    req = st.text_area("Describe the PLC Function (e.g., 'Motor starter with interlock'):")
    if st.button("Generate Function Block"):
        with st.spinner("Generating SCL code..."):
            # Placeholder for your generation logic
            st.code("""
FUNCTION_BLOCK "MotorControl"
VAR_INPUT
    Start : BOOL;
    Stop : BOOL;
END_VAR
            """, language='pascal')
        st.success("Logic generated for authorized user.")
