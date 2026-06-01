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

# 3. Lightweight RAG: Extract PDF Pages into Memory
@st.cache_resource
def load_pdf_text(pdf_path):
    """Reads PDF and stores pages along with page numbers."""
    if not os.path.exists(pdf_path):
        return None
        
    reader = PdfReader(pdf_path)
    pages_data = []
    
    for i, page in enumerate(reader.pages):
        text = page.extract_text()
        if text and text.strip():
            pages_data.append({"page_num": i + 1, "text": text})
            
    return pages_data if pages_data else None

# Load the uploaded PDF document
pdf_filename = "admission_guide.pdf"
pdf_pages = load_pdf_text(pdf_filename)

if pdf_pages:
    st.success(f"📚 Successfully loaded {len(pdf_pages)} pages from '{pdf_filename}'!")

# 4. Handle Chat History
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display previous messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 5. Capture User Input and Search
if user_input := st.chat_input("Ask about Karnataka Diploma admissions..."):
    with st.chat_message("user"):
        st.markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    # Python Search: Find pages that share words with the user's query
    context_from_pdf = ""
    if pdf_pages:
        query_words = set(user_input.lower().split())
        matched_pages = []
        
        for page in pdf_pages:
            # Count how many query words appear on this page
            score = sum(1 for word in query_words if word in page["text"].lower())
            if score > 0:
                matched_pages.append((score, page["text"]))
        
        # Sort by best match and pick top 2 pages
        matched_pages.sort(key=lambda x: x[0], reverse=True)
        top_matches = [text for score, text in matched_pages[:2]]
        context_from_pdf = "\n\n--- Next Page ---\n\n".join(top_matches)

    # Dynamic Persona Instructions
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
            st.error("The server is temporarily busy. Please wait a moment and try again.")
