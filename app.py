import os
import uuid
import requests
import streamlit as st


API_URL = "https://pdf-chatbot-rag-y1lv.onrender.com"


# Create one session ID per browser session
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())


# Store displayed chat messages
if "messages" not in st.session_state:
    st.session_state.messages = []


st.set_page_config(
    page_title="PDF RAG Chatbot",
    page_icon="📄"
)


st.title("📄 PDF RAG Chatbot")

st.write(
    "Upload a PDF and ask questions "
    "based on its contents."
)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.header("💬 Conversation")

    st.caption(
        "Your conversation history is stored using Redis."
    )

    if st.button("🗑️ Clear Chat", use_container_width=True):

        try:

            response = requests.delete(
                f"{API_URL}/memory/{st.session_state.session_id}",
                timeout=30
            )

            if response.ok:

                st.session_state.messages = []

                st.success("Chat memory cleared.")

                st.rerun()

            else:

                st.error(
                    f"Failed to clear memory "
                    f"({response.status_code})"
                )

        except requests.exceptions.RequestException as e:

            st.error(
                f"Backend connection error: {e}"
            )


# ============================================================
# UPLOAD PDF
# ============================================================

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

                st.success(
                    "PDF uploaded successfully."
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


# ============================================================
# CHAT HISTORY
# ============================================================

if st.session_state.messages:

    st.markdown("### 💬 Chat History")

    for message in st.session_state.messages:

        if message["role"] == "user":

            with st.chat_message("user"):

                st.write(message["content"])

        else:

            with st.chat_message("assistant"):

                st.write(message["content"])


# ============================================================
# ASK QUESTION
# ============================================================

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
                        "question": question,
                        "session_id": st.session_state.session_id
                    },

                    timeout=180
                )


            if response.ok:

                data = response.json()

                answer = data["answer"]


                # Save messages for current Streamlit UI
                st.session_state.messages.append(
                    {
                        "role": "user",
                        "content": question
                    }
                )

                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": answer
                    }
                )


                # Display answer
                st.markdown("### 📌 Answer")

                st.write(answer)


                # ====================================================
                # SOURCES
                # ====================================================

                if "sources" in data and data["sources"]:

                    st.markdown("### 📚 Sources")

                    seen_pages = set()

                    for source in data["sources"]:

                        page = source["page"]

                        # Avoid duplicate pages
                        if page in seen_pages:
                            continue

                        seen_pages.add(page)

                        with st.expander(
                            f"📄 Page {page}"
                        ):

                            st.caption(
                                "Relevant passage from your PDF"
                            )

                            st.write(
                                source["excerpt"]
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