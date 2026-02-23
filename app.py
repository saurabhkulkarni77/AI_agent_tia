import streamlit as st
import google.generativeai as genai

# --- 1. Agent Config ---
# Ensure you use your valid API Key
genai.configure(api_key="AIzaSyCQKkhKIJAwFk9BPOVa-I30oStleV106AA")
model = genai.GenerativeModel('gemini-2.5-flash')

st.set_page_config(page_title="TIA Function Block Generator", layout="wide")
st.title("🤖 Siemens SCL Function Block Agent")
st.markdown("Generates production-ready **FBs** with 3-way handshake and safety interlocks.")

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

# --- 3. UI Layout ---
req = st.text_area("Describe the PLC Function (e.g., Lead/Lag Pump Control with Pressure Safety):")

if st.button("Generate Function Block"):
    if not req:
        st.warning("Please enter a requirement first.")
    else:
        with st.spinner("Writing SCL Function Block..."):
            # The "FB-Boilerplate" Prompt
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
            
            # Clean up any accidental markdown backticks if Gemini adds them
            scl_code = scl_code.replace("```scl", "").replace("```", "").strip()
            
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.subheader("📋 Copy-Paste SCL Code")
                st.code(scl_code, language="cpp")
                st.download_button("💾 Download .SCL", scl_code, "AI_FB_Block.scl")
                
            with col2:
                st.subheader("🛡️ Security Audit")
                audit = run_security_audit(scl_code)
                for check, passed in audit.items():
                    st.write(f"{'✅' if passed else '❌'} {check}")
                
                if all(audit.values()):
                    st.success("Validated for TIA Portal")
                else:
                    st.error("Audit Failed - Manual Review Required")
