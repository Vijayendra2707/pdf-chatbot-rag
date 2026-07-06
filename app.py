import os

import requests
import streamlit as st


API_URL = os.getenv(
    "API_URL",
    "http://127.0.0.1:8000"
)

st.set_page_config(
    page_title="PDF RAG Chatbot",
    page_icon="📄"
)

st.title("📄 PDF RAG Chatbot")
st.write("Upload a PDF and ask questions based on its contents.")

st.subheader("📤 Upload PDF")

uploaded_file = st.file_uploader(
    "Choose a PDF file",
    type=["pdf"]
)

if st.button("Upload PDF"):
    if uploaded_file is None:
        st.warning("Please upload a PDF first.")

    else:
        files = {
            "file": (
                uploaded_file.name,
                uploaded_file.getvalue(),
                "application/pdf"
            )
        }

        try:
            with st.spinner("Processing PDF..."):
                response = requests.post(
                    f"{API_URL}/upload",
                    files=files,
                    timeout=120
                )

                response.raise_for_status()

            data = response.json()

            st.success("PDF uploaded and processed successfully.")
            st.write(data["status"])

        except requests.exceptions.RequestException as e:
            st.error(f"Backend connection error: {e}")


st.subheader("💬 Ask Question")

question = st.text_input("Enter your question")

if st.button("Ask"):
    if not question.strip():
        st.warning("Please enter a question.")

    else:
        try:
            with st.spinner("Searching the document..."):
                response = requests.post(
                    f"{API_URL}/ask",
                    json={"question": question},
                    timeout=120
                )

                response.raise_for_status()

            data = response.json()

            st.markdown("### 📌 Answer")
            st.write(data["answer"])

        except requests.exceptions.RequestException as e:
            st.error(f"Backend connection error: {e}")