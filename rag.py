from pypdf import PdfReader
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

chunks = []
vectorizer = None
chunk_vectors = None


def extract_pdf_text(pdf_path: str):
    reader = PdfReader(pdf_path)
    full_text = ""

    for page in reader.pages:
        text = page.extract_text()
        if text:
            full_text += text + "\n"

    return full_text


def split_text(text: str, chunk_size: int = 800, chunk_overlap: int = 100):
    result = []
    start = 0

    while start < len(text):
        end = start + chunk_size
        result.append(text[start:end])
        start += chunk_size - chunk_overlap

    return result


def load_and_create_vector(pdf_path: str):
    global chunks, vectorizer, chunk_vectors

    full_text = extract_pdf_text(pdf_path)

    if not full_text.strip():
        raise ValueError("No readable text found in PDF")

    chunks = split_text(full_text)

    vectorizer = TfidfVectorizer(
        stop_words="english",
        ngram_range=(1, 2),
        max_features=10000
    )

    chunk_vectors = vectorizer.fit_transform(chunks)

    return f"Created search index with {len(chunks)} chunks"


def search(query: str, k: int = 3):
    global chunks, vectorizer, chunk_vectors

    if not chunks or vectorizer is None or chunk_vectors is None:
        return []

    query_vector = vectorizer.transform([query])

    similarities = cosine_similarity(
        query_vector,
        chunk_vectors
    )[0]

    top_indices = similarities.argsort()[::-1][:k]

    results = []

    for index in top_indices:
        if similarities[index] > 0:
            results.append(chunks[index])

    return results