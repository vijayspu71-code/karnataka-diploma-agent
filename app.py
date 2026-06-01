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
    
    # Advanced Text Scanning
    context_from_pdf = ""
    if pdf_pages:
        query_text_lower = user_input.lower()
        query_words = set(query_text_lower.split())
        matched_pages = []
        
        # Check if the user is typing a direct DTE Application ID
        is_application_query = "dte" in query_text_lower
        
        for page in pdf_pages:
            page_text_lower = page["text"].lower()
            score = 0
            
            # CRITICAL MATCH: If searching for an ID, check if it exists on this page explicitly
            if is_application_query:
                # Extract words that look like application numbers (e.g., matching 'dte26')
                for word in query_words:
                    if len(word) > 5 and word in page_text_lower:
                        score += 50  # Massive score boost to lock onto the correct list page
            
            # Standard structural keyword weight
            if "merit" in page_text_lower or "rank" in page_text_lower:
                score += 5
                
            # Count standard word matches
            word_score = sum(1 for word in query_words if word in page_text_lower)
            score += word_score
            
            if score > 0:
                matched_pages.append((score, page["text"]))
        
        # Sort and pull the top matching pages
        matched_pages.sort(key=lambda x: x[0], reverse=True)
        top_matches = [text for score, text in matched_pages[:2]]
        context_from_pdf = "\n\n--- Next Page ---\n\n".join(top_matches)

    # Dynamic Persona Instructions
    SYSTEM_INSTRUCTION = f"""
    You are "Namma Diploma Mitra," an expert AI assistant dedicated to guiding students through the Polytechnic/Diploma admission process in Karnataka.
    
    Use the following verified data block extracted from the uploaded document to answer the query:
    ---
    {context_from_pdf}
    ---
    
    Core Policies:
    - If the user provides an Application ID (like DTE26...), carefully look through the numbers and columns in the data block above.
    - If you find a match, extract and show their corresponding Merit Number / Rank, Name, and category details clearly in a bulleted list.
    - If you still cannot find that specific ID in the text above, politely explain that the matching page might be too dense, and guide them to manually check the official site: https://dtek.karnataka.gov.in.
    - Always answer in a clear, well-structured manner.
    """

    # Generate Agent response
    with st.chat_message("assistant"):
        config = types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            temperature=0.1 # Lower temperature means less guessing, more data precision
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
            st.error("The system is busy right now. Please try your message again.")
