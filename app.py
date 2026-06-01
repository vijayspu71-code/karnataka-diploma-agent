import streamlit as str
from google import genai
from google.genai import types

# 1. Page Configuration and Styling
str.set_page_config(page_title="Namma Diploma Mitra", page_icon="🤖")
str.title("🤖 Namma Diploma Mitra")
str.caption("Your AI Assistant for Karnataka Diploma Admissions")

# 2. Securely get the API Key (will read from Streamlit Secrets later)
api_key = str.secrets.get("GEMINI_API_KEY")

if not api_key:
    str.warning("Please configure your GEMINI_API_KEY in the secrets setting.")
    str.stop()

# Initialize the Gemini Client
client = genai.Client(api_key=api_key)

# 3. Define the Agent's Persona / System Instructions
SYSTEM_INSTRUCTION = """
You are "Namma Diploma Mitra," an expert AI assistant dedicated to guiding students through the Polytechnic/Diploma admission process in Karnataka (managed by the DTE).

Core Policies:
- Technical/Engineering Eligibility: Must pass 10th/SSLC with minimum 35% aggregate.
- Online Merit-based Process: No entrance exam; selection is based on 10th marks.
- Always provide highly structured, bulleted answers.
- Direct users to verify final dates on the official portal: https://dtek.karnataka.gov.in
"""

# 4. Handle Chat History
if "messages" not in str.session_state:
    str.session_state.messages = []

# Display previous messages
for msg in str.session_state.messages:
    with str.chat_message(msg["role"]):
        str.markdown(msg["content"])

# 5. Capture User Input and Respond
if user_input := str.chat_input("Ask about Karnataka Diploma admissions..."):
    # Display user query
    with str.chat_message("user"):
        str.markdown(user_input)
    str.session_state.messages.append({"role": "user", "content": user_input})
    
    # Generate Agent response
    with str.chat_message("assistant"):
        config = types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            temperature=0.3
        )
        
        # Pull history into format Gemini expects
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=user_input,
            config=config
        )
        
        str.markdown(response.text)
        str.session_state.messages.append({"role": "assistant", "content": response.text})
