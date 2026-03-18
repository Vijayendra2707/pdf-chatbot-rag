import streamlit as st
import requests
import time

API_URL = "https://your-fastapi-app.onrender.com"

st.set_page_config(page_title="PDF RAG Chatbot")
st.title("📄 PDF RAG Chatbot")

# Upload section
st.subheader("📤 Upload PDF")

uploaded_file = st.file_uploader("Choose PDF", type=["pdf"])

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
            with st.spinner("Uploading..."):
                res = requests.post(
                    f"{API_URL}/upload",
                    files=files,
                    timeout=120   # ✅ FIXED
                )

            if res.status_code == 200:
                st.success("✅ Uploaded! Processing in background...")

                st.info("⏳ Wait 5–15 seconds before asking questions.")

            else:
                st.error(res.text)

        except Exception as e:
            st.error(f"Error: {e}")


# Ask section
st.subheader("💬 Ask Question")

question = st.text_input("Enter your question")

if st.button("Ask"):
    if question.strip() == "":
        st.warning("Enter a question!")
    else:
        try:
            with st.spinner("Thinking... 🤖"):
                res = requests.post(
                    f"{API_URL}/ask",
                    json={"question": question},
                    timeout=60
                )

            if res.status_code == 200:
                data = res.json()
                st.markdown("### 📌 Answer")
                st.write(data["answer"])
            else:
                st.error(res.text)

        except Exception as e:
            st.error(f"Error: {e}")