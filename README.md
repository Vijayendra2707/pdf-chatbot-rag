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
