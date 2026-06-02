import streamlit as st
import os
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

# 3. High-Capacity Document Loader (Handles Scanned PDFs up to 2GB)
@st.cache_resource
def upload_document_to_gemini(pdf_path):
    if not os.path.exists(pdf_path):
        return None
    
    # Upload directly to Google's API environment which handles OCR automatically
    with open(pdf_path, "rb") as f:
        uploaded_file = client.files.upload(file=pdf_path)
    return uploaded_file

pdf_filename = "admission_guide.pdf"
gemini_file_context = upload_document_to_gemini(pdf_filename)

if gemini_file_context:
    st.success("📚 Document attached directly to Gemini's vision engine!")

# 4. Handle Chat History
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 5. Send Prompt + Full PDF Context to Gemini
if user_input := st.chat_input("Ask about your application ID or merit rank..."):
    with st.chat_message("user"):
        st.markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    SYSTEM_INSTRUCTION = """
    You are "Namma Diploma Mitra," an expert AI assistant guiding students through the Polytechnic/Diploma admission process in Karnataka.
    
    You have been given the official admission/merit PDF document directly. 
    - When a user asks about an Application ID (e.g., DTE262700000962), look through all image rows and data tables in the attached file to find that exact record.
    - Extract and list their corresponding Merit Number, Rank, Name, and category details accurately.
    - If you cannot find the record, request them to double-check their entry numbers.
    - Always answer clearly using structured bullet points.
    """

    with st.chat_message("assistant"):
        try:
            # Pass both the uploaded file reference and the text query in contents
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=[gemini_file_context, user_input],
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_INSTRUCTION,
                    temperature=0.1
                )
            )
            st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
        except Exception as e:
            st.error("The system is busy processing the large document. Please wait a moment and try again.")
