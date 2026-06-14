import streamlit as st
import os
import time
from pypdf import PdfReader
from google import genai
from google.genai import types
# Import the speech recorder component
from streamlit_mic_recorder import speech_to_text

# 1. Check if voice input has data
if "voice_text" in st.session_state and st.session_state.voice_text:
    # Use the text as the query
    user_query = st.session_state.voice_text
    
    # IMPORTANT: Clear it immediately so it doesn't loop on the next rerun
    st.session_state.voice_text = "" 
    
    # Run your document search function here
    # run_search(user_query)Page Configuration and Styling
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

# 3. Dynamic Local PDF Scanner (Intelligent Precise Word Boundary Filtering)
def search_local_pdfs_for_keyword(keyword):
    """Scans local PDFs intelligently by matching exact standalone terms to prevent false early matches."""
    if not keyword:
        return ""
    
    matched_chunks = []
    filler_words = {"what", "is", "the", "of", "name", "merit", "number", "marks", "obtained", "by", "find", "who", "list"}
    
    search_terms = [
        word.lower().strip() for word in keyword.split() 
        if len(word) > 1 and word.lower().strip() not in filler_words
    ]
    
    if not search_terms:
        return ""

    for file in os.listdir("."):
        if file.endswith(".pdf"):
            try:
                reader = PdfReader(file)
                for page_num, page in enumerate(reader.pages):
                    text = page.extract_text()
                    if text:
                        text_lower = text.lower()
                        
                        # Break page into distinct words to verify strict standalone matching
                        words_in_text = text_lower.split()
                        if all(any(term == word.strip(",.-_()[]:;") for word in words_in_text) for term in search_terms):
                            matched_chunks.append(f"\n[Source: {file} | Page: {page_num+1}]\n{text.strip()}")
                        
                        # Accumulate up to 3 highly targeted pages before passing to the model
                        if len(matched_chunks) >= 3:
                            return "\n\n--- Next Section ---\n\n".join(matched_chunks)
            except Exception:
                continue
                
    return "\n\n--- Next Section ---\n\n".join(matched_chunks[:4])

# 4. Handle Chat History
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 5. Dual Input Capture System (Voice + Text Typing)
st.write("---")
st.subheader("🎤 Ask with your Voice")

# Render a simple mic recorder layout button that supports English transcription natively
voice_transcript = speech_to_text(
    start_prompt="Click to start speaking 🎙️",
    stop_prompt="Stop recording 🛑",
    language='en',
    use_container_width=True,
    key='speech'
)

# Text Box Input underneath as an alternative option
typed_input = st.chat_input("Or type your question about merits, exam answers, or dates here...")

# Consolidate input: prioritize voice transcript if captured, otherwise use typed input
user_input = None
if voice_transcript:
    user_input = voice_transcript
elif typed_input:
    user_input = typed_input

# 6. Process Input through Search Index & Gemini Core
if user_input:
    with st.chat_message("user"):
        st.markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    # Give the browser UI a split second to clear its state and keep inputs unlocked
    time.sleep(0.1)
    
    # Process scanning dynamically ONLY when a message is triggered
    with st.spinner("Searching documents..."):
        relevant_context = search_local_pdfs_for_keyword(user_input)
        
        # STRUCTURAL FALLBACK: Look for boundaries like "last", "total", or "end"
        if not relevant_context and any(term in user_input.lower() for term in ["last", "end", "total", "highest", "lowest"]):
            for file in os.listdir("."):
                if file.endswith(".pdf") and "merit" in file.lower():
                    try:
                        reader = PdfReader(file)
                        last_page_idx = len(reader.pages) - 1
                        last_page_text = reader.pages[last_page_idx].extract_text()
                        if last_page_text:
                            relevant_context = f"[Source: {file} | Page: {last_page_idx + 1} (LAST PAGE)]\n{last_page_text.strip()}"
                    except Exception:
                        pass

    SYSTEM_INSTRUCTION = f"""
    You are "Namma Diploma Mitra," an intelligent multi-purpose AI academic assistant for polytechnic and diploma students in Karnataka.
    
    Here is the live, relevant data extracted from the files matching the query:
    ---
    {relevant_context if relevant_context else "No direct document text matched this specific query."}
    ---
    
    Instructions:
    1. MERIT LIST DETAILS: Look closely at the data extracted above. Find the rows corresponding to the user's requested merit number or name. Extract the student name, registration numbers, category, and marks obtained. If it contains the last page data, read the bottom-most rows to identify the final merit number listed in the collection.
    2. GENERAL TOPICS: If the query is about generic concepts (like Arduino or microcontrollers) and no direct text matched above, use your deep native AI intelligence to provide an accurate, helpful answer anyway.
    3. Always reply in clear markdown formatting.
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
            
    # Force a page rerun to refresh the historical chat visual logs cleanly
    st.rerun()
