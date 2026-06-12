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

# 3. Dynamic Local PDF Scanner (Unlocks the main thread instantly)
def search_local_pdfs_for_keyword(keyword):
    """Scans local PDFs on-the-fly for specific keywords to ensure zero thread locking."""
    if not keyword:
        return ""
    
    matched_chunks = []
    search_terms = [word.lower().strip() for word in keyword.split() if len(word) > 3]
    
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
                        # If the page matches any search term, grab it instantly
                        if any(term in text_lower for term in search_terms):
                            matched_chunks.append(f"\n[Source: {file} | Page: {page_num+1}]\n{text.strip()}")
                            # Safety cap: don't overload the context
                            if len(matched_chunks) >= 5:
                                return "\n\n--- Next Section ---\n\n".join(matched_chunks)
            except Exception:
                continue
    return "\n\n--- Next Section ---\n\n".join(matched_chunks)

# 4. Handle Chat History
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Import time at the top of your file
import time

# ... (rest of your configuration and functions)

# 5. Non-Blocking Input Capture
if user_input := st.chat_input("Ask about Madhura's merit, exam answers, or dates..."):
    with st.chat_message("user"):
        st.markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    # Give the browser UI a split second to reset and keep the input text box unlocked
    time.sleep(0.1)
    
    # Process scanning dynamically ONLY when a message is sent
    with st.spinner("Searching documents..."):
        relevant_context = search_local_pdfs_for_keyword(user_input)

    SYSTEM_INSTRUCTION = f"""
    You are "Namma Diploma Mitra," an intelligent multi-purpose AI academic assistant for polytechnic and diploma students in Karnataka.
    
    Here is the live, relevant data extracted from the files matching the query:
    ---
    {relevant_context if relevant_context else "No direct document text matched this specific query."}
    ---
    
    Instructions:
    1. MERIT LISTS: If a student's rank/merit details (like Madhura) are found above, present their Merit Number, ID, Category, and score in clean bullet points.
    2. GENERAL TOPICS: If the query is about generic concepts (like Arduino, engineering, or schedules) and no direct text matched above, use your deep native AI intelligence to provide an accurate, helpful answer anyway.
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
