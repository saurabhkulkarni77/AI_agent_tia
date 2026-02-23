import streamlit as st
import google.generativeai as genai
import streamlit_authenticator as stauth

# --- 1. Security & Authentication Setup ---
try:
    # Convert secrets to dict to allow the authenticator to work (prevents Read-Only error)
    credentials = st.secrets["credentials"].to_dict()
    cookie = st.secrets["cookie"].to_dict()

    authenticator = stauth.Authenticate(
        credentials,
        cookie["name"],
        cookie["key"],
        int(cookie["expiry_days"])
    )
except Exception as e:
    st.error(f"Configuration Error: {e}. Check your Dashboard Secrets!")
    st.stop()

# Version-agnostic login
try:
    result = authenticator.login(label='Login', location='main')
except TypeError:
    result = authenticator.login('main')

if isinstance(result, tuple):
    name, authentication_status, username = result
else:
    name = st.session_state.get("name")
    authentication_status = st.session_state.get("authentication_status")

# --- 2. Security Audit Engine ---
def run_security_audit(code):
    checks = {
        "Block Structure": "FUNCTION_BLOCK" in code.upper() and "END_FUNCTION_BLOCK" in code.upper(),
        "Input Clamping": "LIMIT" in code.upper(),
        "3-Way Handshake": "i_HMI_Confirm" in code,
        "Safety Interlock": "Global_Safety_DB" in code,
        "Memory (Static VAR)": "VAR" in code and "END_VAR" in code
    }
    return checks

# --- 3. Main App Logic ---
if authentication_status:
    authenticator.logout("Logout", "sidebar")
    st.sidebar.success(f"User: {name}")
    
    # Configure Gemini
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel('gemini-2.5-flash')

    st.title("🤖 Siemens SCL Function Block Agent")
    st.markdown("Generates production-ready **FBs** with 3-way handshake and safety interlocks.")

    req = st.text_area("Describe the PLC Function (e.g., Lead/Lag Pump Control with Pressure Safety):")

    if st.button("Generate Function Block"):
        if not req:
            st.warning("Please enter a requirement first.")
        else:
            with st.spinner("Writing SCL Function Block..."):
                prompt = f"""
                Act as a Senior Siemens PLC Developer. Generate a complete Siemens S7-1500 FUNCTION_BLOCK in SCL for: {req}

                STRICT RULES:
                1. Use the syntax: FUNCTION_BLOCK "FB_Generated_Logic"
                2. Define VAR_INPUT: i_AI_Req (Bool), i_HMI_Confirm (Bool), i_System_Ready (Bool), and any process sensors.
                3. Define VAR_OUTPUT: q_Execute (Bool) and any status indicators.
                4. Define VAR (Static): Store the state of the handshake.
                5. First line of code after BEGIN must be: IF NOT "Global_Safety_DB".All_Systems_OK THEN RETURN; END_IF;
                6. Use LIMIT(MN:=, IN:=, MX:=) for all analog scaling or setpoints.
                7. The final output must only trigger if i_AI_Req AND i_HMI_Confirm AND i_System_Ready are ALL true.

                Output ONLY the raw SCL text. No markdown, no backticks.
                """

                response = model.generate_content(prompt)
                scl_code = response.text.strip()

                # Clean up any accidental markdown backticks
                scl_code = scl_code.replace("```scl", "").replace("```", "").strip()
                
                # Store in session state so the download button doesn't wipe the results
                st.session_state.scl_code = scl_code

    # --- Display Results ---
    if "scl_code" in st.session_state:
        scl_code = st.session_state.scl_code
        
        col1, col2 = st.columns([3, 1])

        with col1:
            st.subheader("📋 Copy-Paste SCL Code")
            st.code(scl_code, language="pascal")
            st.download_button(
                label="💾 Download .SCL File",
                data=scl_code,
                file_name="AI_FB_Block.scl",
                mime="text/plain"
            )

        with col2:
            st.subheader("🛡️ Security Audit")
            audit = run_security_audit(scl_code)
            for check, passed in audit.items():
                st.write(f"{'✅' if passed else '❌'} {check}")

            if all(audit.values()):
                st.success("Validated for TIA Portal")
            else:
                st.error("Audit Failed - Manual Review Required")

elif authentication_status == False:
    st.error("Username/password is incorrect")
elif authentication_status == None:
    st.info("Please log in to generate industrial logic.")
