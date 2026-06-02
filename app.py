import streamlit as st
import os
from pypdf import PdfReader
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

# 3. Fast Text Extraction for Small Files
@st.cache_resource
def load_small_pdf(pdf_path):
    if not os.path.exists(pdf_path):
        return ""
    try:
        reader = PdfReader(pdf_path)
        full_text = ""
        for page in reader.pages:
            text = page.extract_text()
            if text:
                full_text += text + "\n\n"
        return full_text.strip()
    except Exception:
        return ""

pdf_filename = "admission_guide.pdf"
document_context = load_small_pdf(pdf_filename)

if document_context:
    st.success("📚 Successfully loaded the admission schedule guide into memory!")
else:
    st.info("👋 Ready to assist! (Note: Reading from general DTE knowledge base if document text isn't parsed)")

# 4. Handle Chat History
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 5. Capture User Input and Respond Instantly
if user_input := st.chat_input("Ask about semester closing dates or application rules..."):
    with st.chat_message("user"):
        st.markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    # Simple, clear instructions matching the text content directly
    SYSTEM_INSTRUCTION = f"""
    You are "Namma Diploma Mitra," an expert AI assistant guiding students through the Polytechnic/Diploma process in Karnataka.
    
    Use the following verified text block extracted from the user's uploaded guide to answer the query:
    ---
    {document_context}
    ---
    
    Core Policies:
    - Look carefully for semester dates, academic schedules, or closing dates inside the text block above.
    - If the exact closing date for the 2nd semester is printed there, state it clearly.
    - If the text block doesn't explicitly name the date, provide the expected window and direct them to verify live updates at https://dtek.karnataka.gov.in.
    - Always answer in clean bullet points.
    """

    with st.chat_message("assistant"):
        try:
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=user_input,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_INSTRUCTION,
                    temperature=0.2
                )
            )
            st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
        except Exception as e:
            st.error("Something went wrong. Please try sending your message again.")
