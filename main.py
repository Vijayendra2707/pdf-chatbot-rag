import os
import shutil

from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from groq import Groq
from pydantic import BaseModel

from rag import load_and_create_vector, search


load_dotenv()

app = FastAPI(title="PDF RAG Chatbot API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise RuntimeError("GROQ_API_KEY environment variable is missing")

client = Groq(api_key=GROQ_API_KEY)

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


class QuestionRequest(BaseModel):
    question: str


@app.get("/")
def health_check():
    return {"status": "API is running"}


@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported"
        )

    pdf_path = os.path.join(UPLOAD_DIR, file.filename)

    try:
        with open(pdf_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        message = load_and_create_vector(pdf_path)

        return {
            "status": message,
            "filename": file.filename
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@app.post("/ask")
def ask_question(req: QuestionRequest):
    if not req.question.strip():
        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty"
        )

    docs = search(req.question, k=3)

    if not docs:
        return {
            "answer": "No relevant information found in the uploaded PDF."
        }

    context = "\n\n---\n\n".join(docs)

    prompt = f"""
You are a document question-answering assistant.

Answer the question ONLY using the provided context.

Rules:
1. Do not use outside knowledge.
2. If the answer is not present in the context, respond exactly:
"Not found in PDF"
3. Give a concise and clear answer.

CONTEXT:
{context}

QUESTION:
{req.question}

ANSWER:
"""

    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.2,
            max_tokens=500
        )

        return {
            "question": req.question,
            "answer": response.choices[0].message.content
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"LLM API error: {str(e)}"
        )