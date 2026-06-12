import streamlit as st
import os
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

# 3. Smart High-Capacity Document Filter (Prevents Token Overflows)
@st.cache_resource
def upload_safe_pdfs_to_gemini():
    uploaded_file_refs = []
    MAX_FILE_SIZE_MB = 15  # Limit local uploads to prevent hitting the 1,048,576 token limit
    
    for file in os.listdir("."):
        if file.endswith(".pdf"):
            try:
                # Check file size before uploading
                file_size_mb = os.path.getsize(file) / (1024 * 1024)
                
                if file_size_mb > MAX_FILE_SIZE_MB:
                    st.warning(f"⚠️ Skipping '{file}' ({file_size_mb:.1f}MB) - File is too large and exceeds token limits.")
                    continue
                    
                # Upload safely sized documents to Google's backend infrastructure
                ref = client.files.upload(file=file)
                uploaded_file_refs.append(ref)
            except Exception:
                continue
    return uploaded_file_refs

# Process files safely into Gemini Cloud storage
with st.spinner("Syncing your document library safely... Please wait."):
    gemini_file_contexts = upload_safe_pdfs_to_gemini()

if gemini_file_contexts:
    st.success(f"📚 Successfully attached {len(gemini_file_contexts)} reference document(s) directly to Gemini's engine!")
else:
    st.info("👋 System ready! Operating using general engineering knowledge base.")

# 4. Handle Chat History
if "messages" not in st.session_state:
    st.session_state.messages = []

# Render chat logs
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 5. Process Input with Direct Media Attachments
if user_input := st.chat_input("Ask about exam answers, dates, or Arduino concepts..."):
    with st.chat_message("user"):
        st.markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    SYSTEM_INSTRUCTION = """
    You are "Namma Diploma Mitra," an intelligent multi-purpose AI academic assistant for polytechnic and diploma students in Karnataka.
    
    You have direct structural access to the safely uploaded PDF documents attached alongside the user query.
    
    Execute your responses based on these rules:
    1. TECHNICAL & EXAM TOPICS: If asked about technical concepts or model answers, scan the corresponding guides to extract accurate criteria points.
    2. GENERAL KNOWLEDGE & LARGE MANUALS: If asked about massive subjects (like deep Arduino programming or full manuals that were too large to load), use your deep native engineering intelligence to give a complete, helpful answer.
    3. PRESENTATION: Always format answers with structured, clean markdown bullet points.
    """

    with st.chat_message("assistant"):
        try:
            # Bundle safe file references along with the user text query
            payload = []
            payload.extend(gemini_file_contexts)
            payload.append(user_input)
            
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=payload,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_INSTRUCTION,
                    temperature=0.2
                )
            )
            st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
            
        except Exception as e:
            # Fallback block to answer general queries even if a file payload triggers an issue
            try:
                fallback_response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=f"Answer this engineering question thoroughly: {user_input}"
                )
                st.markdown(fallback_response.text)
                st.session_state.messages.append({"role": "assistant", "content": fallback_response.text})
            except Exception:
                st.error("Something went wrong. Please refresh and try again.")
