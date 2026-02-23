import streamlit as st
import google.generativeai as genai
import streamlit_authenticator as stauth

# --- 1. Security & Authentication Setup ---
# This pulls the [credentials] and [cookie] sections from your Dashboard Secrets
# --- 1. Security & Authentication Setup ---
try:
    # Convert st.secrets to a real dict using .to_dict() 
    # This prevents the "Secrets does not support item assignment" error
    credentials = st.secrets["credentials"].to_dict()
    cookie = st.secrets["cookie"].to_dict()

    authenticator = stauth.Authenticate(
        credentials,
        cookie["name"],
        cookie["key"],
        int(cookie["expiry_days"]) # Ensure this is an integer
    )
except Exception as e:
    st.error(f"Configuration Error: {e}")
    st.stop()
# Version-agnostic login call (handles v0.2.x and v0.3.x+)
try:
    # Attempt newer version syntax
    result = authenticator.login(label='Login', location='main')
except TypeError:
    # Fallback for older version
    result = authenticator.login('main')

# Handle the return values correctly based on library version
if isinstance(result, tuple):
    name, authentication_status, username = result
else:
    # Some versions update session_state directly
    name = st.session_state.get("name")
    authentication_status = st.session_state.get("authentication_status")
    username = st.session_state.get("username")

# --- 2. Authentication Logic ---
if authentication_status == False:
    st.error("Username/password is incorrect")
elif authentication_status == None:
    st.warning("Please enter your username and password")
elif authentication_status:
    # --- START OF AUTHENTICATED APP ---
    authenticator.logout("Logout", "sidebar")
    st.sidebar.success(f"Welcome {name}")

    # Secure API Config from Secrets
    try:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        model = genai.GenerativeModel('gemini-2.5-flash')
    except Exception:
        st.error("Gemini API Key missing in Dashboard Secrets!")
        st.stop()

    # --- APP CONTENT ---
    st.title("🤖 Siemens SCL Logic Agent")
    
    req = st.text_area("Describe the PLC Function (e.g., 'Motor starter with thermal overload'):")
    
    if st.button("Generate SCL Code"):
        if req:
            with st.spinner("Generating authorized logic..."):
                response = model.generate_content(f"Act as a Siemens PLC Expert. Write SCL code for: {req}")
                st.code(response.text, language='pascal')
        else:
            st.warning("Please describe a function first.")
