import os

import numpy as np
import requests
from pypdf import PdfReader


HF_TOKEN = os.getenv("HF_TOKEN")

if not HF_TOKEN:
    raise RuntimeError(
        "HF_TOKEN environment variable is missing"
    )


MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

EMBEDDING_URL = (
    "https://router.huggingface.co/"
    f"hf-inference/models/{MODEL_NAME}/pipeline/feature-extraction"
)

chunks = []

chunk_vectors = None


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
    chunk_size: int = 1000,
    chunk_overlap: int = 100
):

    result = []

    start = 0

    step = chunk_size - chunk_overlap

    while start < len(text):

        chunk = text[start:start + chunk_size].strip()

        if chunk:
            result.append(chunk)

        start += step

    return result

def get_embeddings(texts):

    response = requests.post(
        EMBEDDING_URL,
        headers={
            "Authorization": f"Bearer {HF_TOKEN}"
        },
        json={
            "inputs": texts,
            "options": {
                "wait_for_model": True
            }
        },
        timeout=180
    )

    if response.status_code != 200:

        raise RuntimeError(
            f"Embedding API error "
            f"{response.status_code}: "
            f"{response.text}"
        )


    embeddings = np.asarray(
        response.json(),
        dtype=np.float32
    )


    # Some feature-extraction APIs can return token-level
    # embeddings instead of one vector per input.
    if embeddings.ndim == 3:
        embeddings = embeddings.mean(axis=1)


    if embeddings.ndim == 1:
        embeddings = embeddings.reshape(1, -1)


    norms = np.linalg.norm(
        embeddings,
        axis=1,
        keepdims=True
    )


    embeddings = embeddings / np.maximum(
        norms,
        1e-12
    )


    return embeddings


def load_and_create_vector(pdf_path: str):

    global chunks, chunk_vectors

    full_text = extract_pdf_text(pdf_path)

    if not full_text.strip():
        raise ValueError("No readable text found in PDF")

    new_chunks = split_text(
        full_text,
        chunk_size=1000,
        chunk_overlap=100
    )

    # Maximum chunks to index
    MAX_CHUNKS = 300

    if len(new_chunks) > MAX_CHUNKS:
        new_chunks = new_chunks[:MAX_CHUNKS]

    vectors = get_embeddings(new_chunks)

    if len(vectors) != len(new_chunks):
        raise RuntimeError(
            "Embedding API returned an unexpected number of vectors"
        )

    chunks = new_chunks
    chunk_vectors = vectors

    return (
        f"Successfully indexed {len(chunks)} document chunks."
    )

def search(query: str, k: int = 3):

    global chunks, chunk_vectors


    if not chunks or chunk_vectors is None:

        return []


    query_vector = get_embeddings(
        [query]
    )[0]


    similarities = (
        chunk_vectors @ query_vector
    )


    k = min(
        k,
        len(chunks)
    )


    top_indices = np.argsort(
        similarities
    )[::-1][:k]


    return [
        chunks[index]
        for index in top_indices
    ]