import streamlit as st
import requests

# ✅ CHANGE THIS AFTER DEPLOYMENT
API_URL = "https://your-fastapi-app.onrender.com"

st.set_page_config(page_title="PDF RAG Chatbot")
st.title("📄 PDF RAG Chatbot")
st.write("Upload a PDF and ask questions from it")

# Upload section
st.subheader("📤 Upload PDF")

uploaded_file = st.file_uploader("Choose a PDF file", type=["pdf"])

if st.button("Upload PDF"):
    if uploaded_file is None:
        st.warning("Please upload a PDF first!")
    else:
        files = {
            "file": (
                uploaded_file.name,
                uploaded_file.getvalue(),
                "application/pdf",
            )
        }
        try:
            with st.spinner("Processing PDF..."):
                res = requests.post(f"{API_URL}/upload", files=files)

            if res.status_code == 200:
                st.success("✅ PDF uploaded & processed successfully!")
            else:
                st.error(f"Upload failed: {res.text}")
        except Exception as e:
            st.error(f"Error connecting to API: {e}")

# Question section
st.subheader("💬 Ask Question")

question = st.text_input("Enter your question")

if st.button("Ask"):
    if question.strip() == "":
        st.warning("Please enter a question!")
    else:
        try:
            with st.spinner("Thinking... 🤖"):
                res = requests.post(
                    f"{API_URL}/ask",
                    json={"question": question},
                    timeout=30
                )

            if res.status_code == 200:
                data = res.json()
                st.markdown("### 📌 Answer")
                st.write(data["answer"])
            else:
                st.error(f"Error: {res.text}")
        except Exception as e:
            st.error(f"Error connecting to API: {e}")