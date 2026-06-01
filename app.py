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
    
    # Improved Search: Matches keywords + structural phrases (e.g., Proforma, Validity)
    context_from_pdf = ""
    if pdf_pages:
        query_text_lower = user_input.lower()
        query_words = set(query_text_lower.split())
        matched_pages = []
        
        for page in pdf_pages:
            page_text_lower = page["text"].lower()
            score = 0
            
            # Scenario A: Exact phrase check (e.g., matching "proforma" or specific numbers)
            if "proforma" in page_text_lower or "validity" in page_text_lower or "ಪ್ರೊಫಾರ್ಮ" in page_text_lower:
                score += 5  # Give high priority to pages mentioning forms explicitly
                
            # Scenario B: Count individual overlapping words
            word_score = sum(2 for word in query_words if word in page_text_lower)
            score += word_score
            
            if score > 0:
                matched_pages.append((score, page["text"]))
        
        # Sort by highest score and merge top matching content blocks
        matched_pages.sort(key=lambda x: x[0], reverse=True)
        top_matches = [text for score, text in matched_pages[:3]] # Pull top 3 pages for broader context
        context_from_pdf = "\n\n--- Next Page ---\n\n".join(top_matches)

    # Dynamic Persona Instructions
    SYSTEM_INSTRUCTION = f"""
    You are "Namma Diploma Mitra," an expert AI assistant dedicated to guiding students through the Polytechnic/Diploma admission process in Karnataka.
    
    Use the following background facts extracted from the official document to answer the user:
    ---
    {context_from_pdf}
    ---
    
    Core Policies:
    - If the user asks about an eligibility certificate, proforma, or validity format, carefully check the context text block above to describe what is written on that page.
    - If you locate the text matching the proforma guidelines, summarize what the student needs to fill out or submit based on the background text.
    - Always provide structured, bulleted answers.
    - Direct users to verify final layouts and print formats on the official portal: https://dtek.karnataka.gov.in.
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
