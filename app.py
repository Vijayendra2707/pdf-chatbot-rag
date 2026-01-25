import streamlit as st
import requests

API_URL = "http://127.0.0.1:8000" 

st.set_page_config(page_title="PDF RAG Chatbot")
st.title("PDF RAG Chatbot")
st.write("Upload a PDF and ask questions from it")

st.subheader("📤 Upload PDF")

uploaded_file = st.file_uploader("Choose a PDF file", type=["pdf"])

if st.button("Upload PDF"):
    if uploaded_file is None:
        st.warning("Please upload a PDF first!")
    else:
        files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
        try:
            res = requests.post(f"{API_URL}/upload", files=files)
            if res.status_code == 200:
                st.success("PDF uploaded & processed successfully!")
                st.json(res.json())
            else:
                st.error(f"Upload failed: {res.text}")
        except Exception as e:
            st.error(f"Error connecting to API: {e}")

st.subheader("Ask Question")

question = st.text_input("Enter your question")

if st.button("Ask"):
    if question.strip() == "":
        st.warning("Please enter a question!")
    else:
        try:
            payload = {"question": question}
            res = requests.post(f"{API_URL}/ask", json=payload)

            if res.status_code == 200:
                data = res.json()
                st.markdown("### Answer")
                st.write(data["answer"])
            else:
                st.error(f"Error: {res.text}")
        except Exception as e:
            st.error(f"Error connecting to API: {e}")
