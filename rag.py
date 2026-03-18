from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

db = None
def load_and_create_vector(pdf_path: str):
    global db

    reader = PdfReader(pdf_path)
    full_text = ""

    for page in reader.pages:
        text = page.extract_text()
        if text:
            full_text+=text+"\n"
    
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=100
    )
    chunks =splitter.split_text(full_text)

    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

    db = FAISS.from_texts(chunks,embeddings)

def search(query: str, k: int = 3):
    global db

    if db is None:
        return []
    results = db.similarity_search(query=query,k=k)
    return [doc.page_content for doc in results]