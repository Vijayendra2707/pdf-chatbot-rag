# 📄 PDF RAG Chatbot

A lightweight **Retrieval-Augmented Generation (RAG)** chatbot that allows users to upload PDF documents and ask questions based on their content.

The application extracts and chunks PDF text, generates semantic embeddings using the **Hugging Face Inference API**, retrieves relevant document chunks using **NumPy cosine similarity**, and uses **Groq Llama 3.1** to generate context-aware answers.

Built using **FastAPI** for the backend and **Streamlit** for the frontend.

---

## 🚀 Live Demo

[![Live Demo](https://img.shields.io/badge/Live%20Demo-Try%20Now-brightgreen)](https://pdf-chatbot-rag-simple.streamlit.app)

[![API Docs](https://img.shields.io/badge/FastAPI-API%20Docs-blue)](https://pdf-chatbot-rag-y1lv.onrender.com/docs)

**🌐 Live Application:**  
https://pdf-chatbot-rag-simple.streamlit.app

**📘 Backend API Documentation:**  
https://pdf-chatbot-rag-y1lv.onrender.com/docs

> **Note:** The hosted application may take 30–60 seconds to wake up after being inactive because it is deployed on the free Render plan.

---

## ✨ Features

- 📤 Upload PDF documents
- 📄 Extract text using `pypdf`
- ✂️ Automatic chunking with overlap
- 🧠 Semantic embeddings using Hugging Face Inference API
- 🔍 Context retrieval using cosine similarity
- ⚡ Answer generation using Groq Llama 3.1
- 💬 Interactive Streamlit interface
- 🎯 Answers generated only from retrieved document context
- 🚫 Returns **"Not found in PDF"** when information is unavailable
- 🐳 Dockerized deployment
- ☁️ Deployable on Render

# 🧠 How It Works

The chatbot follows a Retrieval-Augmented Generation (RAG) workflow.

1. User uploads a PDF document.
2. Text is extracted using **pypdf**.
3. The extracted text is divided into overlapping chunks.
4. Each chunk is converted into semantic embeddings using the **Hugging Face Inference API**.
5. Embeddings are normalized and stored in memory.
6. User submits a question.
7. The question is embedded using the same embedding model.
8. Cosine similarity identifies the most relevant document chunks.
9. Retrieved chunks are sent to **Groq Llama 3.1**.
10. The generated answer is displayed in the Streamlit interface.

---

# 🏗️ System Architecture

```text
                    User
                      │
                      ▼
               Streamlit UI
                      │
          HTTP Requests (REST API)
                      │
                      ▼
               FastAPI Backend
                      │
          ┌───────────┴───────────┐
          │                       │
          ▼                       ▼
     Upload PDF            User Question
          │                       │
          ▼                       ▼
      PDF Parsing         Question Embedding
        (pypdf)       (Hugging Face API)
          │                       │
          ▼                       │
     Text Chunking                │
          │                       │
          ▼                       │
Document Embeddings               │
(Hugging Face API)                │
          │                       │
          ▼                       │
      NumPy Vectors ◄─────────────┘
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
        Response
```

---

# 🛠️ Tech Stack

| Category | Technology |
|----------|------------|
| Programming Language | Python |
| Backend Framework | FastAPI |
| Frontend Framework | Streamlit |
| LLM | Groq (Llama 3.1) |
| Embeddings | Hugging Face Inference API |
| Retrieval | NumPy Cosine Similarity |
| PDF Processing | pypdf |
| API Communication | Requests |
| Deployment | Render |
| Containerization | Docker |
| Version Control | Git & GitHub |

---

# 📁 Project Structure

```text
pdf-chatbot-rag/
│
├── app.py                 # Streamlit frontend
├── main.py                # FastAPI backend
├── rag.py                 # PDF processing & semantic retrieval
├── requirements.txt       # Python dependencies
├── Dockerfile             # Docker configuration
├── .gitignore
├── README.md
│
├── uploads/               # Temporary uploaded PDFs
│
└── images/                # README screenshots
    ├── home.png
    ├── upload.png
    └── chat.png
```

---

# ⚙️ Environment Variables

Create a `.env` file in the project root.

```env
GROQ_API_KEY=your_groq_api_key
HF_TOKEN=your_huggingface_token
```

For the deployed Streamlit frontend, configure:

```env
API_URL=https://pdf-chatbot-rag-y1lv.onrender.com
```

> **Note:** Never commit your `.env` file to GitHub.

---

# 🚀 Running Locally

## 1️⃣ Clone the repository

```bash
git clone https://github.com/Vijayendra2707/pdf-chatbot-rag.git

cd pdf-chatbot-rag
```

---

## 2️⃣ Install dependencies

```bash
pip install -r requirements.txt
```

---

## 3️⃣ Configure environment variables

Create a `.env` file:

```env
GROQ_API_KEY=your_groq_api_key
HF_TOKEN=your_huggingface_token
```

---

## 4️⃣ Start the FastAPI backend

```bash
python -m uvicorn main:app --reload
```

Open:

```
http://127.0.0.1:8000/docs
```

---

## 5️⃣ Start the Streamlit frontend

Open another terminal:

```bash
streamlit run app.py
```

The application will open automatically in your browser.

---

# 🔌 API Endpoints

## Health Check

```http
GET /
```

Returns the API status.

---

## Upload PDF

```http
POST /upload
```

Uploads a PDF document, extracts text, generates embeddings, and creates the semantic search index.

---

## Ask Question

```http
POST /ask
```

### Request

```json
{
    "question": "What is the document about?"
}
```

### Response

```json
{
    "answer": "..."
}
```

---

# 🐳 Docker Deployment

## Build Docker Image

```bash
docker build -t pdf-rag-chatbot .
```

---

## Run Container

```bash
docker run -p 8000:8000 \
-e GROQ_API_KEY=your_groq_api_key \
-e HF_TOKEN=your_huggingface_token \
pdf-rag-chatbot
```

---
# ⚠️ Current Limitations

- The application currently indexes **one PDF at a time**.
- Uploading a new PDF replaces the previously indexed document.
- Document embeddings are stored **in memory**, so they are lost when the backend restarts.
- Scanned PDFs without embedded text are not currently supported (OCR is not implemented).
- The Hugging Face Inference API requires a valid API token and an internet connection.
- Response quality depends on the retrieved document chunks and embedding model.

---

# 🚀 Future Improvements

Planned enhancements include:

- 📚 Multi-document support
- 🗂️ Persistent vector storage
- 👤 User authentication
- 💬 Conversational memory for follow-up questions
- 📄 Page number citations in responses
- 🔍 Hybrid Retrieval (Semantic + Keyword Search)
- ⚡ Retrieval reranking for improved accuracy
- 🖼️ OCR support for scanned PDFs
- 📊 Document summarization
- 🌍 Multi-language document support
- ☁️ Cloud object storage integration (AWS S3 / Azure Blob)
- 📈 Analytics dashboard
- 🔄 CI/CD pipeline using GitHub Actions

---

# 📈 Performance

| Metric | Value |
|---------|--------|
| Embedding Model | Hugging Face Inference API |
| LLM | Groq Llama 3.1 |
| Retrieval | Cosine Similarity |
| Vector Storage | In-memory NumPy Arrays |
| API Framework | FastAPI |
| UI Framework | Streamlit |

---

# 💡 Learning Outcomes

This project helped demonstrate practical knowledge of:

- Retrieval-Augmented Generation (RAG)
- Semantic Search
- LLM Integration
- REST API Development with FastAPI
- Streamlit Application Development
- Docker Containerization
- Cloud Deployment using Render
- PDF Processing
- Prompt Engineering
- Git & GitHub Workflow

---

# 🤝 Contributing

Contributions, issues, and feature requests are welcome.

If you'd like to contribute:

1. Fork the repository
2. Create a new feature branch

```bash
git checkout -b feature/your-feature
```

3. Commit your changes

```bash
git commit -m "Add new feature"
```

4. Push your branch

```bash
git push origin feature/your-feature
```

5. Open a Pull Request

---

# 👨‍💻 Author

## Vijayendra Rane

Computer Science Engineering Student | AI • Machine Learning • Generative AI

- GitHub: https://github.com/Vijayendra2707

---
