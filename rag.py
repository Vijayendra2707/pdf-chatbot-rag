from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_community.vectorstores import FAISS
import os


embeddings = SentenceTransformerEmbeddings(
    model_name="all-MiniLM-L6-v2"
)

db = None
INDEX_PATH = "faiss_index"

def load_and_create_vector(pdf_path: str):
    global db

    reader = PdfReader(pdf_path)
    full_text = ""

    for page in reader.pages:
        text = page.extract_text()
        if text:
            full_text += text + "\n"

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=100
    )

    chunks = splitter.split_text(full_text)

    # ✅ Create or update DB
    if db is None:
        db = FAISS.from_texts(chunks, embeddings)
    else:
        db.add_texts(chunks)

    # ✅ Save to disk (IMPORTANT)
    db.save_local(INDEX_PATH)

    return "Vector DB created successfully"


def load_db():
    global db

    if os.path.exists(INDEX_PATH):
        db = FAISS.load_local(
            INDEX_PATH,
            embeddings,
            allow_dangerous_deserialization=True
        )


def search(query: str, k: int = 3):
    global db

    if db is None:
        return []

    results = db.similarity_search(query=query, k=k)
    return [doc.page_content for doc in results]