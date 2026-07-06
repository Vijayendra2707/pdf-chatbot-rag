from typing import Optional

import numpy as np
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer


chunks = []

chunk_vectors: Optional[np.ndarray] = None


MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


embedding_model = SentenceTransformer(MODEL_NAME)


def extract_pdf_text(pdf_path: str) -> str:

    reader = PdfReader(pdf_path)

    pages = []

    for page in reader.pages:

        text = page.extract_text()

        if text:

            pages.append(text)

    return "\n".join(pages)


def split_text(
    text: str,
    chunk_size: int = 700,
    chunk_overlap: int = 100
):

    result = []

    start = 0

    text_length = len(text)

    step = chunk_size - chunk_overlap

    while start < text_length:

        end = start + chunk_size

        chunk = text[start:end].strip()

        if chunk:

            result.append(chunk)

        start += step

    return result


def load_and_create_vector(pdf_path: str):

    global chunks, chunk_vectors

    full_text = extract_pdf_text(pdf_path)

    if not full_text.strip():

        raise ValueError(
            "No readable text found in PDF"
        )

    chunks = split_text(full_text)

    if not chunks:

        raise ValueError(
            "No chunks were created from the PDF"
        )

    chunk_vectors = embedding_model.encode(
        chunks,
        batch_size=8,
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=False
    ).astype(np.float32)

    return (
        f"Created semantic search index "
        f"with {len(chunks)} chunks"
    )


def search(query: str, k: int = 3):

    global chunks, chunk_vectors

    if not chunks or chunk_vectors is None:

        return []

    query_vector = embedding_model.encode(
        query,
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=False
    ).astype(np.float32)

    similarities = chunk_vectors @ query_vector

    k = min(k, len(chunks))

    top_indices = np.argsort(similarities)[::-1][:k]

    return [
        chunks[index]
        for index in top_indices
    ]