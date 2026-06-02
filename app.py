import streamlit as st
import os
from pypdf import PdfReader
from google import genai
from google.genai import types

# 1. Page Configuration and Styling
st.set_page_config(page_title="Namma Diploma Mitra", page_icon="🤖", layout="centered")
st.title("🤖 Namma Diploma Mitra")
st.caption("Your Multi-Purpose AI Academic & Admission Assistant")

# 2. Securely get the API Key from Streamlit Secrets
api_key = st.secrets.get("GEMINI_API_KEY")
if not api_key:
    st.warning("Please configure your GEMINI_API_KEY in the Streamlit secrets setting.")
    st.stop()

# Initialize the Gemini Client
client = genai.Client(api_key=api_key)

# 3. High-Efficiency Text Extraction
@st.cache_resource
def load_pdf_context(pdf_path):
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
    except Exception as e:
        return ""

# Read your uploaded PDF file
pdf_filename = "admission_guide.pdf"
document_context = load_pdf_context(pdf_filename)

if document_context:
    st.success("📚 Successfully loaded the document reference guide into memory!")
else:
    st.info("👋 System ready! Operating using global engineering and DTE knowledge base.")

# 4. Handle Chat History
if "messages" not in st.session_state:
    st.session_state.messages = []

# Render existing chat logs
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 5. Capture User Input and Process Intelligently
if user_input := st.chat_input("Ask about exam answers, dates, or application rules..."):
    with st.chat_message("user"):
        st.markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    # Advanced System Instructions allowing dynamic behavioral routing
    SYSTEM_INSTRUCTION = f"""
    You are "Namma Diploma Mitra," an intelligent multi-purpose AI academic assistant for polytechnic and diploma students in Karnataka.
    
    You have access to a background reference document context block:
    ---
    {document_context}
    ---
    
    Execute your responses based on these smart routing rules:
    1. TECHNICAL & EXAM QUESTIONS: If the user asks engineering questions (e.g., about Microcontrollers, Assembly languages, LCDs, or Relays), deeply analyze the document context above. If the matching question or answer blueprint is there, format it beautifully with clean points and code blocks.
    2. KNOWLEDGE EXPANSION: If the user asks a technical question that is only partially addressed or missing in the 2-page document (like expanding on missing diagrams or pin definitions), use your broader foundational engineering intelligence to provide a comprehensive, complete response. 
    3. ADMISSION & SCHEDULE DETAILS: If asked about schedules, notifications, or ranks, check the text. If not found, provide guidance and direct them to check live updates at the official portal: https://dtek.karnataka.gov.in.
    4. TONE: Always maintain a supportive, crisp, and educational presentation style using markdown bullet points.
    """

    with st.chat_message("assistant"):
        try:
            # Primary structural request using system personas and context boundaries
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
            # Smart Fallback loop: If custom context parameters cause an API conflict, 
            # bypass boundaries and answer using raw native AI engineering capability.
            try:
                fallback_response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=f"Answer this technical engineering/diploma question thoroughly: {user_input}"
                )
                st.markdown(fallback_response.text)
                st.session_state.messages.append({"role": "assistant", "content": fallback_response.text})
            except Exception as final_error:
                st.error("Connection timed out. Please try sending your message again.")
