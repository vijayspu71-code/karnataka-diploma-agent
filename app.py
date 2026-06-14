import streamlit as st
import os
import time
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

# 3. Dynamic Local PDF Scanner (Intelligent Precise Word Boundary Filtering)
def search_local_pdfs_for_keyword(keyword):
    """Scans local PDFs intelligently by matching exact standalone terms to prevent false early matches."""
    if not keyword:
        return ""
        
    matched_chunks = []
    filler_words = {"what", "is", "the", "of", "name", "merit", "number", "marks", "obtained", "by", "find", "who", "list"}
    search_terms = [word.lower().strip() for word in keyword.split() if len(word) > 1 and word.lower().strip() not in filler_words]
    
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

# 4. Handle and Display Chat History
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    if msg.get("content"):  # Render only valid messages
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

# 5. Chat Input Capture
if user_input := st.chat_input("Ask about Madhura's merit, exam answers, or dates..."):
    # Immediately render the user's message on the screen
    with st.chat_message("user"):
        st.markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    # Tiny pause to let Streamlit's UI components switch seamlessly
    time.sleep(0.1)
    
    # Process scanning dynamically ONLY when a message is sent
    with st.spinner("Searching documents..."):
        relevant_context = search_local_pdfs_for_keyword(user_input)
        
        # STRUCTURAL FALLBACK: If looking for boundaries like "last", "total", or "end" 
        # and search came up empty, pull the very last page of the PDF into the context!
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

    # Dynamic Instructions injected into the LLM logic
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
            # Map conversation history safely for the new google-genai SDK format
            formatted_contents = []
            for msg in st.session_state.messages:
                # CRITICAL SAFETY: Skip empty messages or old error blocks to prevent payload crashing
                if not msg.get("content") or "Something went wrong" in msg["content"]:
                    continue
                    
                # API requires "model" instead of "assistant"
                api_role = "model" if msg["role"] == "assistant" else "user"
                formatted_contents.append(
                    types.Content(
                        role=api_role,
                        parts=[types.Part.from_text(text=msg["content"])]
                    )
                )

            # Request generation with the properly structured payload bundle
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=formatted_contents,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_INSTRUCTION,
                    temperature=0.1
                )
            )
            
            # Print response to the app container and append to the session history log
            if response.text:
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
            else:
                st.error("Received an empty response from the model. Please try again.")
            
        except Exception as e:
            # Send the real traceback error to your background terminal logs for easier tracking
            print(f"Gemini API Execution Failure: {e}")
            st.error("Something went wrong. Please try sending your message again.")
