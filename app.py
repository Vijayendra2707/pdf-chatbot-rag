import os

import requests
import streamlit as st


API_URL ="https://pdf-chatbot-rag-y1lv.onrender.com"


st.set_page_config(
    page_title="PDF RAG Chatbot",
    page_icon="📄"
)


st.title("📄 PDF RAG Chatbot")

st.write(
    "Upload a PDF and ask questions "
    "based on its contents."
)


st.subheader("📤 Upload PDF")


uploaded_file = st.file_uploader(
    "Choose a PDF file",
    type=["pdf"]
)


if st.button("Upload PDF"):

    if uploaded_file is None:

        st.warning(
            "Please upload a PDF first."
        )


    else:

        try:

            with st.spinner(
                "Processing PDF..."
            ):

                response = requests.post(

                    f"{API_URL}/upload",

                    files={
                        "file": (
                            uploaded_file.name,
                            uploaded_file.getvalue(),
                            "application/pdf"
                        )
                    },

                    timeout=240
                )


            if response.ok:

                data = response.json()

                st.write(
                    data["status"]
                )


            else:

                try:

                    detail = response.json().get(
                        "detail",
                        response.text
                    )

                except ValueError:

                    detail = response.text


                st.error(
                    f"Backend error "
                    f"({response.status_code}): "
                    f"{detail}"
                )


        except requests.exceptions.RequestException as e:

            st.error(
                f"Backend connection error: {e}"
            )


st.subheader("💬 Ask Question")


question = st.text_input(
    "Enter your question"
)


if st.button("Ask"):

    if not question.strip():

        st.warning(
            "Please enter a question."
        )


    else:

        try:

            with st.spinner(
                "Searching the document..."
            ):

                response = requests.post(

                    f"{API_URL}/ask",

                    json={
                        "question": question
                    },

                    timeout=180
                )


            if response.ok:

                st.markdown(
                    "### 📌 Answer"
                )

                st.write(
                    response.json()["answer"]
                )


            else:

                try:

                    detail = response.json().get(
                        "detail",
                        response.text
                    )

                except ValueError:

                    detail = response.text


                st.error(
                    f"Backend error "
                    f"({response.status_code}): "
                    f"{detail}"
                )


        except requests.exceptions.RequestException as e:

            st.error(
                f"Backend connection error: {e}"
            )