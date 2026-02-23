%%writefile app.py
import streamlit as st
import google.generativeai as genai

# --- 1. Secure Config ---
# This looks for the key in your Streamlit Cloud settings, NOT in the code.
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=API_KEY)
except Exception:
    st.error("Missing API Key! Please add 'GEMINI_API_KEY' to your Streamlit Secrets.")
    st.stop()

model = genai.GenerativeModel('gemini-1.5-flash')

st.set_page_config(page_title="TIA Function Block Generator", layout="wide")
st.title("🤖 Siemens SCL Function Block Agent")

# --- 2. Security Audit Engine ---
def run_security_audit(code):
    checks = {
        "FB Structure": "FUNCTION_BLOCK" in code.upper(),
        "Input Clamping": "LIMIT" in code.upper(),
        "3-Way Handshake": "i_HMI_Confirm" in code,
        "Safety Interlock": "Global_Safety_DB" in code,
        "Memory (Static VAR)": "VAR" in code and "END_VAR" in code
    }
    return checks

# --- 3. UI Layout ---
req = st.text_area("Describe the PLC Function:")

if st.button("Generate Function Block"):
    if not req:
        st.warning("Please enter a requirement.")
    else:
        with st.spinner("Writing SCL..."):
            prompt = f"Generate a Siemens S7-1500 FUNCTION_BLOCK in SCL for: {req}. Include 3-way handshake, LIMIT() for analogs, and check 'Global_Safety_DB'.All_Systems_OK. Output ONLY code."
            
            response = model.generate_content(prompt)
            scl_code = response.text.replace("```scl", "").replace("```", "").strip()
            
            col1, col2 = st.columns([3, 1])
            with col1:
                st.subheader("📋 Copy-Paste SCL Code")
                st.code(scl_code, language="cpp")
            
            with col2:
                st.subheader("🛡️ Security Audit")
                audit = run_security_audit(scl_code)
                for check, passed in audit.items():
                    st.write(f"{'✅' if passed else '❌'} {check}")
