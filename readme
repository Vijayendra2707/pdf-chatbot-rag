📄 PDF RAG Chatbot

A lightweight **Retrieval-Augmented Generation (RAG) chatbot** that allows users to upload PDF documents and ask questions based on their content.

The application extracts and chunks PDF text, generates semantic embeddings using the **Hugging Face Inference API**, retrieves relevant document chunks using **cosine similarity**, and uses **Groq Llama 3.1** to generate context-grounded answers.

The project uses **FastAPI** for the backend API and **Streamlit** for the user interface.

🚀 Live Demo

Try the deployed application:

**Live Application:** https://pdf-chatbot-rag-simple.streamlit.app

**Backend API Docs:** https://pdf-chatbot-rag-y1lv.onrender.com//docs

[![Live Demo](https://img.shields.io/badge/Live%20Demo-Open%20Application-success)](https://pdf-chatbot-rag-simple.streamlit.app)

[![API Docs](https://img.shields.io/badge/FastAPI-API_Docs-blue)](https://pdf-chatbot-rag-y1lv.onrender.com//docs)

✨ Features

* 📤 Upload and process PDF documents
* 📄 Extract text using `pypdf`
* ✂️ Split documents into overlapping text chunks
* 🧠 Generate semantic embeddings using the Hugging Face Inference API
* 🔍 Retrieve relevant chunks using NumPy cosine similarity
* ⚡ Generate answers using Groq Llama 3.1
* 💬 Interactive Streamlit user interface
* 🎯 Answers are generated only from retrieved PDF context
* 🚫 Returns `Not found in PDF` when the answer is unavailable in the retrieved context
* 🐳 Dockerized deployment support
* ☁️ Designed for lightweight cloud deployment

---

🧠 How It Works

The application follows a Retrieval-Augmented Generation pipeline:

1. The user uploads a PDF document.

2. Text is extracted from the PDF using `pypdf`.

3. The extracted text is divided into overlapping chunks.

4. Each chunk is sent to the Hugging Face Inference API to generate semantic embeddings.

5. The embedding vectors are normalized and stored in memory as NumPy arrays.

6. When the user asks a question:

   * The question is converted into an embedding.
   * Cosine similarity is calculated between the question embedding and document embeddings.
   * The top-k most relevant chunks are retrieved.
   * Retrieved chunks are combined into context.
   * The context and question are sent to Groq Llama 3.1.
   * The generated answer is returned to the user.

🏗️ Architecture

                    User
                      │
                      ▼
               Streamlit UI
                      │
                      │ HTTP Requests
                      ▼
                FastAPI Backend
                      │
            ┌─────────┴─────────┐
            │                   │
            ▼                   ▼
       PDF Upload          User Question
            │                   │
            ▼                   ▼
     Text Extraction     Question Embedding
         (pypdf)         (Hugging Face API)
            │                   │
            ▼                   │
      Text Chunking             │
            │                   │
            ▼                   │
    Document Embeddings         │
    (Hugging Face API)          │
            │                   │
            ▼                   │
       NumPy Vectors ◄──────────┘
            │
            ▼
      Cosine Similarity
            │
            ▼
    Top-K Relevant Chunks
            │
            ▼
       Context + Question
            │
            ▼
       Groq Llama 3.1
            │
            ▼
           Answer

🛠️ Tech Stack

| Component            | Technology                 |
| -------------------- | -------------------------- |
| Programming Language | Python                     |
| Backend              | FastAPI                    |
| Frontend             | Streamlit                  |
| LLM                  | Groq Llama 3.1             |
| Embeddings           | Hugging Face Inference API |
| Retrieval            | NumPy Cosine Similarity    |
| PDF Parsing          | pypdf                      |
| API Communication    | Requests                   |
| Containerization     | Docker                     |
| Deployment           | Render                     |

📁 Project Structure

pdf-chatbot-rag/
│
├── app.py
├── main.py
├── rag.py
├── requirements.txt
├── Dockerfile
├── .gitignore
└── README.md

⚙️ Environment Variables

Create a `.env` file in the project root:

```text
GROQ_API_KEY=your_groq_api_key
HF_TOKEN=your_huggingface_token
```

The `.env` file should not be committed to GitHub.

For the deployed Streamlit frontend, configure:

```text
API_URL=https://your-backend-service-url
```

🚀 Running Locally

1. Clone the repository

```bash
git clone YOUR_REPOSITORY_URL
cd pdf-chatbot-rag
```

2. Install dependencies

```bash
pip install -r requirements.txt
```

3. Configure environment variables

Create a `.env` file and add:

```text
GROQ_API_KEY=your_groq_api_key
HF_TOKEN=your_huggingface_token
```

4. Start the FastAPI backend

```bash
python -m uvicorn main:app --reload
```

The API documentation will be available at:

```text
http://127.0.0.1:8000/docs
```

5. Start the Streamlit frontend

Open another terminal and run:

```bash
streamlit run app.py
```

🔌 API Endpoints

Health Check

```text
GET /
```

Checks whether the FastAPI backend is running.

Upload PDF

```text
POST /upload
```

Uploads a PDF, extracts its text, generates embeddings, and creates the in-memory semantic search index.

Ask Question

```text
POST /ask
```

Retrieves relevant PDF chunks and generates an answer using Groq Llama 3.1.

Example request:

```json
{
  "question": "What is the main topic of the document?"
}
```

🐳 Docker Deployment

Build the Docker image:

```bash
docker build -t pdf-rag-chatbot .
```

Run the container:

```bash
docker run -p 8000:8000 \
  -e GROQ_API_KEY=your_groq_api_key \
  -e HF_TOKEN=your_huggingface_token \
  pdf-rag-chatbot
```

⚠️ Current Limitations

* The application currently maintains one active PDF index per backend instance.
* Document embeddings are stored in memory and are lost when the backend restarts.
* Uploading another PDF replaces the previously indexed document.
* Scanned PDFs without an embedded text layer are not supported because OCR is not currently implemented.
* Retrieval quality depends on the embedding model and the selected top-k chunks.
* The Hugging Face Inference API requires network access and valid API credentials.

🔮 Future Improvements

* Support multiple PDFs and document collections
* Add persistent vector storage
* Introduce document IDs and user sessions
* Add OCR support for scanned PDFs
* Add source citations and page numbers to generated answers
* Implement hybrid semantic and keyword retrieval
* Add reranking for improved retrieval accuracy
* Add conversational memory for follow-up questions
* Improve frontend chat history and document management
* Add automated testing and CI/CD

👨‍💻 Author

**Vijayendra Rane**

Built as a Generative AI and Retrieval-Augmented Generation project demonstrating semantic search, API-based embedding generation, LLM integration, FastAPI backend development, Streamlit UI development, Docker containerization, and cloud deployment.
