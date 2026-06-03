import os
import time
import streamlit as st
from google import genai
from google.genai import types
from google.genai.errors import APIError

# 1. Initialize the Gemini Client
if "GEMINI_API_KEY" not in os.environ:
    st.error("Please set the GEMINI_API_KEY environment variable.")
    st.stop()

client = genai.Client()

# Define the documents
DOCUMENT_FILES = ["admission_guide.pdf", "merit_list.pdf"]

# 2. Optimized File Upload (Saves Quota using Session State)
if "uploaded_contexts" not in st.session_state:
    st.session_state.uploaded_contexts = []
    
    with st.spinner("Processing admission documents... Please wait."):
        uploaded_refs = []
        for file_name in DOCUMENT_FILES:
            if os.path.exists(file_name):
                try:
                    # Uploading files to the File API counts towards your daily usage,
                    # so we ensure it ONLY happens once per session.
                    uploaded_file = client.files.upload(file=file_name)
                    uploaded_refs.append(uploaded_file)
                except Exception as e:
                    st.error(f"Failed to upload {file_name}: {e}")
            else:
                st.warning(f"File not found: {file_name}")
        
        st.session_state.uploaded_contexts = uploaded_refs
        if uploaded_refs:
            st.success(f"Successfully loaded {len(uploaded_refs)} reference files!")

# 3. Streamlit Chat UI Setup
st.title("📌 Karnataka Diploma Admission Assistant")
st.write("Ask queries regarding diploma admissions, cut-offs, and merit lists.")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hello! I have read the admission guide and merit list. How can I help you today?"}
    ]

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 4. Handle User Input
if user_query := st.chat_input("Enter your question here:"):
    
    # Display user message immediately
    with st.chat_message("user"):
        st.markdown(user_query)
    st.session_state.messages.append({"role": "user", "content": user_query})

    # Generate response from Gemini
    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        response_placeholder.markdown("Thinking...")
        
        try:
            # Reconstruct our content payload
            content_payload = []
            content_payload.extend(st.session_state.uploaded_contexts)
            content_payload.append(user_query)
            
            system_instruction = (
                "You are an expert student counselor assisting with Karnataka Diploma Admissions. "
                "Use the provided admission guide and merit list documents to give precise, helpful answers."
            )

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
            
        except APIError as e:
            # Elegant handling for your 429 quota block
            if e.code == 429:
                error_msg = "⚠️ **Quota Exceeded (429):** You've hit the Gemini Free Tier limit (20 requests/day). Please wait a bit or switch to a pay-as-you-go API key."
            else:
                error_msg = f"API Error occurred: {e.message}"
            
            response_placeholder.markdown(error_msg)
            st.session_state.messages.append({"role": "assistant", "content": error_msg})
            
        except Exception as e:
            error_msg = f"An unexpected error occurred: {e}"
            response_placeholder.markdown(error_msg)
            st.session_state.messages.append({"role": "assistant", "content": error_msg})
