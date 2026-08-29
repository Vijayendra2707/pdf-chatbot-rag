import os
import shutil

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi import File
from fastapi import HTTPException
from fastapi import UploadFile
from groq import Groq
from pydantic import BaseModel


load_dotenv()


from rag import load_and_create_vector
from rag import search


app = FastAPI(
    title="PDF RAG Chatbot API"
)


GROQ_API_KEY = os.getenv(
    "GROQ_API_KEY"
)


if not GROQ_API_KEY:

    raise RuntimeError(
        "GROQ_API_KEY environment variable is missing"
    )


client = Groq(
    api_key=GROQ_API_KEY
)


UPLOAD_DIR = "uploads"


os.makedirs(
    UPLOAD_DIR,
    exist_ok=True
)


class QuestionRequest(BaseModel):

    question: str


@app.get("/")
def health_check():

    return {
        "status": "API is running"
    }


@app.post("/upload")
async def upload_pdf(
    file: UploadFile = File(...)
):

    if (
        not file.filename
        or not file.filename.lower().endswith(".pdf")
    ):

        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported"
        )


    safe_filename = os.path.basename(
        file.filename
    )


    pdf_path = os.path.join(
        UPLOAD_DIR,
        safe_filename
    )


    try:

        with open(pdf_path, "wb") as buffer:

            shutil.copyfileobj(
                file.file,
                buffer
            )


        message = load_and_create_vector(
            pdf_path
        )


        return {
            "status": message,
            "filename": safe_filename
        }


    except ValueError as e:

        raise HTTPException(
            status_code=400,
            detail=str(e)
        )


    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


    finally:

        try:
            await file.close()
        except Exception:
            pass

        try:
            if os.path.exists(pdf_path):
                os.remove(pdf_path)
        except OSError:
            pass


@app.post("/ask")
def ask_question(
    req: QuestionRequest
):

    question = req.question.strip()


    if not question:

        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty"
        )


    try:

        docs = search(
            question,
            k=3
        )


    except Exception as e:

        raise HTTPException(
            status_code=502,
            detail=f"Embedding API error: {e}"
        )


    if not docs:

        raise HTTPException(
            status_code=409,
            detail=(
                "No PDF is currently indexed. "
                "Upload a PDF first."
            )
        )


    context = "\n\n---\n\n".join(
        docs
    )


    prompt = f"""
You are a document question-answering assistant.

Answer the user's question using ONLY the provided PDF context.

Rules:

1. Do not use outside knowledge.

2. If the answer is not present in the provided context, respond exactly:

Not found in PDF

3. Give a concise and clear answer.

4. Do not invent information.

PDF CONTEXT:

{context}


USER QUESTION:

{question}


ANSWER:
"""


    try:

        response = client.chat.completions.create(

            model="openai/gpt-oss-120b",

            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],

            temperature=0,

            max_tokens=400
        )


        answer = (
            response
            .choices[0]
            .message
            .content
        )


        return {
            "question": question,
            "answer": answer
        }


    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"LLM API error: {e}"
        )
