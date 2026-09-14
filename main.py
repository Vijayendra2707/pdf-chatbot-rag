import os
import shutil
import json
from memory import get_memory
from memory import add_message
from memory import clear_memory
import time
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
    session_id: str


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

def rewrite_question(question: str, history: list):

    if not history:
        return question

    conversation = "\n".join(
        f"{message['role']}: {message['content']}"
        for message in history
    )

    prompt = f"""
Rewrite the latest user question using the conversation history.

The rewritten question must:
- be a complete standalone question
- preserve the user's original intent
- resolve references such as "it", "this", "that", "what about", etc.
- NOT answer the question
- NOT add new information

Conversation:
{conversation}

Latest question:
{question}

Return ONLY the complete rewritten question.
"""

    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0,
        max_tokens=150
    )

    rewritten = (
        response
        .choices[0]
        .message
        .content
        .strip()
    )

    # Safety fallback
    if len(rewritten) < 10:
        return question

    return rewritten

def route_question(question: str, history: list):

    conversation = "\n".join(
        f"{message['role'].upper()}: {message['content']}"
        for message in history[-6:]
    )

    prompt = f"""
Classify the user's question into exactly ONE route.

Routes:

DOCUMENT
Use DOCUMENT when the answer requires information from the uploaded PDF.

CONVERSATION
Use CONVERSATION when the answer requires only previous conversation history.

BOTH
Use BOTH when the answer requires both the PDF and previous conversation history.

NONE
Use NONE when the question requires neither the PDF nor conversation history.

Question:
{question}

Conversation history:
{conversation}

Return ONLY ONE WORD from these four options:

DOCUMENT
CONVERSATION
BOTH
NONE
"""

    try:

        response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a routing classifier. "
                        "Return ONLY ONE WORD: "
                        "DOCUMENT, CONVERSATION, BOTH, or NONE."
                    )
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0,
            max_tokens=20,
            reasoning_effort="low"
        )

        raw = response.choices[0].message.content

        print("\n===== ROUTER DEBUG =====")
        print("Question:", question)
        print("Raw:", repr(raw))
        print("Finish:", response.choices[0].finish_reason)
        print("========================")

        if not raw:
            print("Router returned empty response.")
            return "DOCUMENT"

        route = raw.strip().upper()

        # Handle accidental extra text from the model
        for valid_route in [
            "CONVERSATION",
            "DOCUMENT",
            "BOTH",
            "NONE"
        ]:
            if valid_route in route:
                return valid_route

        print("Invalid route returned:", repr(route))

    except Exception as e:
        print("Router error:", e)

    return "DOCUMENT"

@app.post("/ask")
def ask_question(req: QuestionRequest):

    total_start = time.perf_counter()

    question = req.question.strip()
    session_id = req.session_id.strip()

    if not session_id:
        raise HTTPException(
            status_code=400,
            detail="Session ID cannot be empty"
        )

    if not question:
        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty"
        )

    rewrite_time = 0.0
    retrieval_time = 0.0
    llm_time = 0.0

    # ---------------------------------------------------------
    # 1. Get conversation history
    # ---------------------------------------------------------
    router_start = time.perf_counter()

    history = get_memory(session_id)

    # ---------------------------------------------------------
    # 2. Decide what information source is required
    # ---------------------------------------------------------

    route = route_question(question, history)

    router_time = (
        time.perf_counter() - router_start
    ) * 1000

    print(f"Router time: {router_time:.2f} ms")

    print("\nQuestion:", question)
    print("History:", history)
    print("Route:", route)

    # =========================================================
    # CONVERSATION ONLY
    # =========================================================
    if route == "CONVERSATION":

        if not history:

            total_time = (
                time.perf_counter() - total_start
            ) * 1000

            print(
                "\n===== PERFORMANCE ====="
            )
            print(f"Router:     {router_time:.2f} ms")
            print(f"Rewrite:    {rewrite_time:.2f} ms")
            print(f"Retrieval:  {retrieval_time:.2f} ms")
            print(f"LLM:        {llm_time:.2f} ms")
            print(f"TOTAL:      {total_time:.2f} ms")
            print("=======================\n")

            return {
                "question": question,
                "answer": "I don't have any conversation history yet.",
                "sources": [],
                "metrics": {
                    "route": route,
                    "router_time_ms": router_time,
                    "rewrite_time_ms": rewrite_time,
                    "retrieval_time_ms": retrieval_time,
                    "llm_time_ms": llm_time,
                    "total_time_ms": total_time
                }
            }

        conversation = "\n".join(
            f"{message['role'].upper()}: {message['content']}"
            for message in history
        )

        prompt = f"""
You are a conversational assistant.

Answer the user's question using ONLY the conversation
history below.

Do not use the PDF.
Do not use outside knowledge.
Do not invent information.

CONVERSATION HISTORY:

{conversation}

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
                max_tokens=300
            )

            answer = (
                response
                .choices[0]
                .message
                .content
                .strip()
            )

        except Exception as e:

            raise HTTPException(
                status_code=500,
                detail=f"LLM API error: {e}"
            )

        add_message(
            session_id,
            "user",
            question
        )

        add_message(
            session_id,
            "assistant",
            answer
        )

        return {
            "question": question,
            "answer": answer,
            "sources": []
        }

    # =========================================================
    # NONE
    # =========================================================

    if route == "NONE":

        answer = (
            "I can only answer questions using the "
            "uploaded PDF and the current conversation."
        )

        add_message(
            session_id,
            "user",
            question
        )

        add_message(
            session_id,
            "assistant",
            answer
        )

        total_time = (
            time.perf_counter() - total_start
        ) * 1000

        print(
            "\n===== PERFORMANCE ====="
        )

        print(f"Router:     {router_time:.2f} ms")
        print(f"Rewrite:    {rewrite_time:.2f} ms")
        print(f"Retrieval:  {retrieval_time:.2f} ms")
        print(f"LLM:        {llm_time:.2f} ms")
        print(f"TOTAL:      {total_time:.2f} ms")

        print(
            "=======================\n"
        )

        return {
            "question": question,
            "answer": answer,
            "sources": [],
            "metrics": {
                "route": route,
                "router_time_ms": router_time,
                "rewrite_time_ms": rewrite_time,
                "retrieval_time_ms": retrieval_time,
                "llm_time_ms": llm_time,
                "total_time_ms": total_time
            }
        }

    # =========================================================
    # DOCUMENT / BOTH
    # =========================================================

    if route == "BOTH":

        rewrite_start = time.perf_counter()

        search_question = rewrite_question(
            question,
            history
        )

        rewrite_time = (
            time.perf_counter() - rewrite_start
        ) * 1000

        print(
            "Original question:",
            question
        )

        print(
            "Rewritten question:",
            search_question
        )

        print(
            f"Rewrite time: "
            f"{rewrite_time:.2f} ms"
        )

    else:

        # DOCUMENT route
        search_question = question

    # ---------------------------------------------------------
    # 3. Hybrid RAG retrieval
    # ---------------------------------------------------------

    try:

        retrieval_start = time.perf_counter()

        docs = search(
            search_question,
            k=3,
            candidate_k=10
        )

    except Exception as e:

        raise HTTPException(
            status_code=502,
            detail=f"Retrieval error: {e}"
        )

    retrieval_time = (
        time.perf_counter() - retrieval_start
    ) * 1000

    print(
        f"Retrieval time: "
        f"{retrieval_time:.2f} ms"
    )

    if not docs:

        raise HTTPException(
            status_code=409,
            detail=(
                "No PDF is currently indexed. "
                "Upload a PDF first."
            )
        )

    # ---------------------------------------------------------
    # 4. Build PDF context
    # ---------------------------------------------------------

    context = "\n\n---\n\n".join(
        f"[Page {doc['page']}]\n{doc['text']}"
        for doc in docs
    )

    # ---------------------------------------------------------
    # 5. Conversation context
    # ---------------------------------------------------------

    conversation = "\n".join(
        f"{message['role'].upper()}: {message['content']}"
        for message in history
    )

    # =========================================================
    # BOTH → history helps understand the question
    # DOCUMENT → PDF is sufficient
    # =========================================================

    if route == "BOTH":

        prompt = f"""
You are a conversational document question-answering assistant.

Answer the user's question using the conversation history
and the provided PDF context.

Rules:

1. Use conversation history ONLY to understand the user's intent
   and references.

2. Use the PDF context for factual information.

3. Do not use outside knowledge.

4. If the answer is not present in the PDF context, respond exactly:

Not found in PDF

5. Do not invent information.

6. Give a concise and clear answer.

CONVERSATION HISTORY:

{conversation}

PDF CONTEXT:

{context}

USER QUESTION:

{question}

ANSWER:
"""

    else:

        prompt = f"""
You are a document question-answering assistant.

Answer the user's question using ONLY the provided PDF context.

Rules:

1. Do not use outside knowledge.

2. If the answer is not present in the provided context,
   respond exactly:

Not found in PDF

3. Give a concise and clear answer.

4. Do not invent information.

PDF CONTEXT:

{context}

USER QUESTION:

{question}

ANSWER:
"""

    # ---------------------------------------------------------
    # 6. Final LLM answer
    # ---------------------------------------------------------

    try:

        llm_start = time.perf_counter()

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

        llm_time = (
            time.perf_counter() - llm_start
        ) * 1000

        print(
            f"LLM time: "
            f"{llm_time:.2f} ms"
        )

        answer = (
            response
            .choices[0]
            .message
            .content
            .strip()
        )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"LLM API error: {e}"
        )

    # ---------------------------------------------------------
    # 7. Save conversation
    # ---------------------------------------------------------

    add_message(
        session_id,
        "user",
        question
    )

    add_message(
        session_id,
        "assistant",
        answer
    )

    # ---------------------------------------------------------
    # 8. Return answer + sources
    # ---------------------------------------------------------

    total_time = (
        time.perf_counter() - total_start
    ) * 1000

    print(
        "\n===== PERFORMANCE ====="
    )

    print(
        f"Router:     {router_time:.2f} ms"
    )

    print(
        f"Rewrite:    {rewrite_time:.2f} ms"
    )

    print(
        f"Retrieval:  {retrieval_time:.2f} ms"
    )

    print(
        f"LLM:        {llm_time:.2f} ms"
    )

    print(
        f"TOTAL:      {total_time:.2f} ms"
    )

    print(
        "=======================\n"
    )

    return {
        "question": question,
        "answer": answer,
        "sources": [
            {
                "page": doc["page"],
                "excerpt": doc["excerpt"]
            }
            for doc in docs[:3]
        ],
        "metrics": {
            "route": route,
            "router_time_ms": router_time,
            "rewrite_time_ms": rewrite_time,
            "retrieval_time_ms": retrieval_time,
            "llm_time_ms": llm_time,
            "total_time_ms": total_time
        }
    }

@app.delete("/memory/{session_id}")
def delete_memory(session_id: str):

    clear_memory(session_id)

    return {
        "status": "Conversation memory cleared"
    }