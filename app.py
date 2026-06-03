import os
import streamlit as st
from google import genai
from google.genai import types

# 1. Initialize the Gemini Client
# Make sure you have GEMINI_API_KEY set in your environment variables
if "GEMINI_API_KEY" not in os.environ:
    st.error("Please set the GEMINI_API_KEY environment variable.")
    st.stop()

client = genai.Client()

# 2. Define the documents to look for
DOCUMENT_FILES = ["admission_guide.pdf", "merit_list.pdf"]

@st.cache_resource
def upload_documents_to_gemini():
    """Uploads both PDF files to the Gemini File API and returns their references."""
    uploaded_refs = []
    for file_name in DOCUMENT_FILES:
        if os.path.exists(file_name):
            st.info(f"Loading and processing {file_name}...")
            try:
                # Upload the file to Gemini File API
                uploaded_file = client.files.upload(file=file_name)
                uploaded_refs.append(uploaded_file)
            except Exception as e:
                st.error(f"Failed to upload {file_name}: {e}")
        else:
            st.warning(f"File not found: {file_name}. Please ensure it is in the repository.")
    
    if not uploaded_refs:
        st.error("No documents were successfully loaded. The bot might lack context.")
    else:
        st.success(f"Successfully cached {len(uploaded_refs)} document(s) in Gemini context!")
    
    return uploaded_refs

# Load/Upload files (Streamlit caches this so it doesn't re-upload on every click)
uploaded_contexts = upload_documents_to_gemini()

# 3. Streamlit UI Setup
st.title("📌 Karnataka Diploma Admission Assistant")
st.write("Ask queries regarding diploma admissions, cut-offs, guidelines, and merit lists.")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hello! I have read the admission guide and merit list. How can I help you with your Karnataka Diploma admission process today?"}
    ]

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 4. Handle User Input
if user_query := st.chat_input("Enter your question here (e.g., What is the cutoff for computer science?):"):
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(user_query)
    st.session_state.messages.append({"role": "user", "content": user_query})

    # Generate response from Gemini
    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        response_placeholder.markdown("Thinking...")
        
        try:
            # Injecting both documents directly into the contents list alongside the prompt
            content_payload = []
            content_payload.extend(uploaded_contexts)
            content_payload.append(user_query)
            
            system_instruction = (
                "You are an expert student counselor assisting with Karnataka Diploma Admissions. "
                "Use the provided admission guide and merit list documents to give precise, helpful, "
                "and accurate answers. If the information is not present in either document, state that politely."
            )

            # Request generation from Gemini 2.5 Flash (excellent for multimodal text/PDFs)
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=content_payload,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.3,
                )
            )
            
            ai_response = response.text
            response_placeholder.markdown(ai_response)
            st.session_state.messages.append({"role": "assistant", "content": ai_response})
            
        except Exception as e:
            error_msg = f"An error occurred while generating a response: {e}"
            response_placeholder.markdown(error_msg)
            st.session_state.messages.append({"role": "assistant", "content": error_msg})
