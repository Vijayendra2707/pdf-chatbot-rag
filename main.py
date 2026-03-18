from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel
import shutil
import os
import threading

from groq import Groq
from dotenv import load_dotenv
from rag import load_and_create_vector, search, load_db

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="PDF RAG Chatbot")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

UPLOAD_PDF = "uploads"
os.makedirs(UPLOAD_PDF, exist_ok=True)

# ✅ Load existing FAISS DB on startup
load_db()


class QuestionRequest(BaseModel):
    question: str


@app.get("/")
def check():
    return {"status": "API is running"}


# ✅ Background processing (NO TIMEOUT)
def process_pdf(pdf_path):
    load_and_create_vector(pdf_path)


@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    pdf_path = os.path.join(UPLOAD_PDF, file.filename)

    with open(pdf_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # ⚡ Run in background thread
    threading.Thread(target=process_pdf, args=(pdf_path,)).start()

    return {
        "status": "Processing started",
        "filename": file.filename
    }


@app.post("/ask")
def ask_questions(req: QuestionRequest):
    docs = search(req.question, k=3)

    if not docs:
        return {"answer": "No PDF processed yet. Please upload and wait."}

    context = "\n\n".join(docs)

    prompt = f"""
You are a helpful assistant.
Answer ONLY using the given context.
If answer not found, say: "Not found in PDF".

Context:
{context}

Question:
{req.question}
"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )

    return {
        "question": req.question,
        "answer": response.choices[0].message.content
    }