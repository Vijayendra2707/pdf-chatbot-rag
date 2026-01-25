from fastapi import FastAPI, UploadFile,File
from pydantic import BaseModel
import shutil
import os 

from groq import Groq
from dotenv import load_dotenv
from rag import load_and_create_vector,search

load_dotenv()
app =FastAPI(title="PDF search and answer")
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
UPLOAD_PDF = "uploads"
os.makedirs(UPLOAD_PDF,exist_ok=True)

class QuestionRequest(BaseModel):
    question: str


@app.get("/")
def check():
    return {
        "Status":"API is running "
    }

@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    pdf_path = os.path.join(UPLOAD_PDF,file.filename)
    with open(pdf_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    msg = load_and_create_vector(pdf_path)
    return {
        "Status":msg,
        "filename": file.filename
    }

@app.post("/ask")
def ask_questions(req: QuestionRequest):
    docs = search(req.question, k=3)
    if not docs:
        return{"answer":"No pdf uploaded yet ."}
    
    context = "\n\n".join(docs)

    prompt=f"""
You are a helpful assistant.
Answer the following question ONLY based on the context given below .
If the answer is not found in the context just say: "Not found in PDF".

Context is :
{context}

Question is :
{req.question}
"""
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role":"user","content": prompt}
        ],
        temperature=0.2
    )

    return {
        "question": req.question,
        "answer": response.choices[0].message.content
    }