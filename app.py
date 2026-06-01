import streamlit as st
from google import genai
from google.genai import types

# 1. Page Configuration and Styling
st.set_page_config(page_title="Namma Diploma Mitra", page_icon="🤖")
st.title("🤖 Namma Diploma Mitra")
st.caption("Your AI Assistant for Karnataka Diploma Admissions")

# 2. Securely get the API Key from Streamlit Secrets
api_key = st.secrets.get("GEMINI_API_KEY")

if not api_key:
    st.warning("Please configure your GEMINI_API_KEY in the secrets setting.")
    st.stop()

# Initialize the Gemini Client
client = genai.Client(api_key=api_key)

# 3. Define the Agent's Persona / System Instructions
SYSTEM_INSTRUCTION = f"""
    You are "Namma Diploma Mitra," an expert AI assistant dedicated to guiding students through the Polytechnic/Diploma admission process in Karnataka.
    
    Use the following verified background facts extracted from the official PDF documents to answer the user accurately:
    ---
    {context_from_pdf}
    ---
    
    Core Policies:
    - For 2026 Timelines / Last Date to Apply: Inform the user that applications typically open in mid-May and usually close around mid-to-late June 2026. 
    - If you cannot find the exact, absolute deadline date in the PDF text above, explicitly instruct the user to check the live "Notification and Circulars" tab on the official DTE portal: https://dtek.karnataka.gov.in.
    - Always provide structured, bulleted answers.
    - Keep your tone highly reassuring and helpful.
    """

# 4. Handle Chat History
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display previous messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 5. Capture User Input and Respond
if user_input := st.chat_input("Ask about Karnataka Diploma admissions..."):
    # Display user query
    with st.chat_message("user"):
        st.markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    # Generate Agent response
    with st.chat_message("assistant"):
        config = types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            temperature=0.3
        )
        
        try:
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=user_input,
                config=config
            )
            st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
        except Exception as e:
            st.error("The server is temporarily busy or rate-limited. Please wait a moment and try submitting your message again.")
      
