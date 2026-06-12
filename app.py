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

# 3. Smart Local Text Extractor (Bypasses File Upload Bottlenecks)
@st.cache_resource
def load_all_local_pdfs():
    combined_text = ""
    for file in os.listdir("."):
        if file.endswith(".pdf"):
            try:
                reader = PdfReader(file)
                # If it's the giant merit list, extract text cleanly
                for page_num, page in enumerate(reader.pages):
                    text = page.extract_text()
                    if text:
                        # Add structural markers so Gemini knows where it is looking
                        combined_text += f"\n[File: {file} | Page: {page_num+1}]\n" + text
            except Exception:
                continue
    return combined_text

with st.spinner("Reading your local PDF files into memory... Please wait."):
    all_document_text = load_all_local_pdfs()

if all_document_text:
    st.success("📚 Successfully loaded all document data into the local knowledge base!")
else:
    st.info("👋 System ready! Operating using general engineering knowledge base.")

# 4. Handle Chat History
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 5. Capture User Input & Narrow Down the Search Context
if user_input := st.chat_input("Ask about Madhura's merit, exam answers, or dates..."):
    with st.chat_message("user"):
        st.markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    # Intelligent Search: If looking for a specific student name or ID, 
    # extract only the pages from the giant text that contain that keyword!
    relevant_context = ""
    query_keyword = user_input.lower().strip()
    
    # Try to find specific name keywords (e.g., "madhura" or a DTE ID)
    search_terms = [word for word in query_keyword.split() if len(word) > 3]
    
    if all_document_text and search_terms:
        # Split data by our page markers
        pages_data = all_document_text.split("[File:")
        matched_chunks = []
        
        for chunk in pages_data:
            chunk_lower = chunk.strip().lower()
            if chunk_lower and any(term in chunk_lower for term in search_terms):
                matched_chunks.append("[File:" + chunk)
        
        # Merge only the matching pages to keep token count extremely small and fast
        relevant_context = "\n\n--- Relevant Page ---\n\n".join(matched_chunks[:5])
    
    # Fallback to a safe snippet if no explicit name match is found
    if not relevant_context and all_document_text:
        relevant_context = all_document_text[:20000] # Safe text chunk limit

    SYSTEM_INSTRUCTION = f"""
    You are "Namma Diploma Mitra," an intelligent multi-purpose AI academic assistant for polytechnic and diploma students in Karnataka.
    
    Here is the filtered, highly relevant data extracted from the uploaded files (including merit lists and guides):
    ---
    {relevant_context}
    ---
    
    Execute your responses based on these rules:
    1. MERIT LIST & STUDENT QUERIES: If the user asks about a student's rank or merit number (like Madhura), carefully scan the rows in the text block above. Locate the name, extract her Merit Number, Application ID, Category, and score details, and print them clearly.
    2. COGNITIVE FALLBACK: If the student name is missing from the specific text blocks above, use your intelligence to politely ask the user to provide their application ID or exact spelling to help locate them.
    3. PRESENTATION: Always format answers with structured, clean markdown bullet points.
    """

    with st.chat_message("assistant"):
        try:
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=user_input,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_INSTRUCTION,
                    temperature=0.1
                )
            )
            st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
            
        except Exception as e:
            st.error("Something went wrong. Please try sending your message again.")
           
