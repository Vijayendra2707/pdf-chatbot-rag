import os
import re
import numpy as np
import requests
from pypdf import PdfReader
from rank_bm25 import BM25Okapi
import time
import json

HF_TOKEN = os.getenv("HF_TOKEN")

HF_HEADERS = {
    "Authorization": f"Bearer {HF_TOKEN}"
}

if not HF_TOKEN:
    raise RuntimeError(
        "HF_TOKEN environment variable is missing"
    )


MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

RERANKER_URL = "https://vj2707-context-rag-reranker.hf.space"

EMBEDDING_URL = (
    "https://router.huggingface.co/"
    f"hf-inference/models/{MODEL_NAME}/pipeline/feature-extraction"
)

def rerank_documents(query, documents):
    response = requests.post(
        f"{RERANKER_URL}/gradio_api/call/rerank",
        json={
            "data": [
                query,
                "\n\n".join(documents)
            ]
        },
        headers=HF_HEADERS,
        timeout=60
    )

    response.raise_for_status()

    event_id = response.json()["event_id"]

    result = requests.get(
        f"{RERANKER_URL}/gradio_api/call/rerank/{event_id}",
        headers=HF_HEADERS,
        timeout=60
    )

    result.raise_for_status()

    return result.json()


# --------------------------------------------------
# GLOBAL INDEXES
# --------------------------------------------------

chunks = []
chunk_vectors = None
bm25_index = None


# --------------------------------------------------
# PDF EXTRACTION
# --------------------------------------------------

def extract_pdf_pages(pdf_path: str):

    reader = PdfReader(pdf_path)

    pages = []

    for page_number, page in enumerate(reader.pages, start=1):

        text = page.extract_text()

        if text and text.strip():

            pages.append({
                "page": page_number,
                "text": text.strip()
            })

    return pages


# --------------------------------------------------
# CHUNKING
# --------------------------------------------------

def split_text(
    text: str,
    chunk_size: int = 500,
    chunk_overlap: int = 50
):

    result = []

    start = 0

    step = chunk_size - chunk_overlap

    while start < len(text):

        chunk = text[
            start:start + chunk_size
        ].strip()

        if chunk:
            result.append(chunk)

        start += step

    return result


def get_relevant_excerpt(query: str, text: str, max_chars: int = 350):
    """
    Extract the most relevant sentence(s) from a retrieved chunk
    for displaying as a source citation.
    """

    sentences = re.split(
        r'(?<=[.!?])\s+',
        text.strip()
    )

    query_words = set(
        re.findall(
            r'\b[a-zA-Z0-9]+\b',
            query.lower()
        )
    )

    scored_sentences = []

    for sentence in sentences:

        sentence_words = set(
            re.findall(
                r'\b[a-zA-Z0-9]+\b',
                sentence.lower()
            )
        )

        score = len(
            query_words.intersection(sentence_words)
        )

        scored_sentences.append(
            (score, sentence.strip())
        )

    # Highest relevance first
    scored_sentences.sort(
        key=lambda x: x[0],
        reverse=True
    )

    selected = []
    current_length = 0

    for score, sentence in scored_sentences:

        if not sentence:
            continue

        if current_length + len(sentence) > max_chars:
            continue

        selected.append(sentence)
        current_length += len(sentence)

    if not selected:
        return text[:max_chars].strip() + "..."

    return " ".join(selected)


# --------------------------------------------------
# EMBEDDINGS
# --------------------------------------------------
def get_embeddings(texts):

    if isinstance(texts, str):
        texts = [texts]

    response = requests.post(
        EMBEDDING_URL,
        headers={
            "Authorization": f"Bearer {HF_TOKEN}",
            "Content-Type": "application/json"
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

    data = response.json()

    # Convert API response to numpy
    embeddings = np.asarray(data, dtype=np.float32)

    # --------------------------------------------------
    # HANDLE DIFFERENT HF RESPONSE SHAPES
    # --------------------------------------------------

    # Case 1:
    # Multiple texts -> token-level embeddings
    # shape: (num_texts, tokens, dimensions)
    if embeddings.ndim == 3:
        embeddings = embeddings.mean(axis=1)

    # Case 2:
    # Multiple texts -> sentence embeddings
    # shape: (num_texts, dimensions)
    elif embeddings.ndim == 2:
        pass

    # Case 3:
    # Single text -> embedding vector
    # shape: (dimensions,)
    elif embeddings.ndim == 1:
        embeddings = embeddings.reshape(1, -1)

    else:
        raise RuntimeError(
            f"Unexpected embedding shape: {embeddings.shape}"
        )

    # --------------------------------------------------
    # CHECK NUMBER OF VECTORS
    # --------------------------------------------------

    if embeddings.shape[0] != len(texts):

        # If only one text was supplied and HF returned
        # a token-level structure that wasn't caught above
        if len(texts) == 1:
            embeddings = embeddings.reshape(1, -1)

        else:
            raise RuntimeError(
                f"Expected {len(texts)} embeddings, "
                f"but received shape {embeddings.shape}"
            )

    # --------------------------------------------------
    # NORMALIZE
    # --------------------------------------------------

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

# --------------------------------------------------
# TOKENIZATION FOR BM25
# --------------------------------------------------

def tokenize(text: str):

    return text.lower().split()


# --------------------------------------------------
# BUILD INDEX
# --------------------------------------------------

def load_and_create_vector(pdf_path: str):

    global chunks
    global chunk_vectors
    global bm25_index


    pages = extract_pdf_pages(
        pdf_path
    )


    if not pages:

        raise ValueError(
            "No readable text found in PDF"
        )


    new_chunks = []


    # Create chunks while preserving page number
    for page_data in pages:

        page_chunks = split_text(
            page_data["text"],
            chunk_size=1000,
            chunk_overlap=100
        )


        for chunk in page_chunks:

            new_chunks.append({

                "text": chunk,

                "page": page_data["page"]

            })


    if not new_chunks:

        raise ValueError(
            "No chunks could be created from PDF"
        )


    # ----------------------------------------------
    # DENSE INDEX
    # ----------------------------------------------


    chunk_texts = [
        item["text"]
        for item in new_chunks
    ]


    vectors = get_embeddings(
        chunk_texts
    )


    if len(vectors) != len(new_chunks):

        raise RuntimeError(
            "Embedding API returned an "
            "unexpected number of vectors"
        )


    # ----------------------------------------------
    # BM25 INDEX
    # ----------------------------------------------

    tokenized_chunks = [
        tokenize(text)
        for text in chunk_texts
    ]


    new_bm25_index = BM25Okapi(
        tokenized_chunks
    )


    # ----------------------------------------------
    # SAVE INDEXES
    # ----------------------------------------------

    chunks = new_chunks

    chunk_vectors = vectors

    bm25_index = new_bm25_index


    return (
        f"Successfully indexed "
        f"{len(chunks)} document chunks."
    )


# --------------------------------------------------
# RECIPROCAL RANK FUSION
# --------------------------------------------------

def reciprocal_rank_fusion(
    dense_indices,
    bm25_indices,
    k=60
):

    scores = {}


    # Dense ranking
    for rank, index in enumerate(
        dense_indices
    ):

        scores[index] = scores.get(
            index,
            0
        ) + 1 / (k + rank + 1)


    # BM25 ranking
    for rank, index in enumerate(
        bm25_indices
    ):

        scores[index] = scores.get(
            index,
            0
        ) + 1 / (k + rank + 1)


    ranked_indices = sorted(
        scores,
        key=scores.get,
        reverse=True
    )


    return ranked_indices


# --------------------------------------------------
# HYBRID SEARCH
# --------------------------------------------------

def search(
    query: str,
    k: int = 3,
    candidate_k: int = 5
):

    global chunks
    global chunk_vectors
    global bm25_index

    if (
        not chunks
        or chunk_vectors is None
        or bm25_index is None
    ):
        return []

    # ==============================================
    # TOTAL RETRIEVAL TIMER
    # ==============================================

    total_start = time.perf_counter()

    # ==============================================
    # 1. QUERY EMBEDDING
    # ==============================================

    start = time.perf_counter()

    query_vector = get_embeddings(
        [query]
    )[0]

    embedding_time = (
        time.perf_counter() - start
    ) * 1000

    # ==============================================
    # 2. DENSE RETRIEVAL
    # ==============================================

    start = time.perf_counter()

    dense_scores = (
        chunk_vectors @ query_vector
    )

    dense_candidate_count = min(
        candidate_k,
        len(chunks)
    )

    dense_indices = np.argsort(
        dense_scores
    )[::-1][
        :dense_candidate_count
    ]

    dense_time = (
        time.perf_counter() - start
    ) * 1000

    # ==============================================
    # 3. BM25 RETRIEVAL
    # ==============================================

    start = time.perf_counter()

    tokenized_query = tokenize(
        query
    )

    bm25_scores = bm25_index.get_scores(
        tokenized_query
    )

    bm25_candidate_count = min(
        candidate_k,
        len(chunks)
    )

    bm25_indices = np.argsort(
        bm25_scores
    )[::-1][
        :bm25_candidate_count
    ]

    bm25_time = (
        time.perf_counter() - start
    ) * 1000

    # ==============================================
    # 4. RECIPROCAL RANK FUSION
    # ==============================================

    start = time.perf_counter()

    fused_indices = reciprocal_rank_fusion(
        dense_indices,
        bm25_indices
    )

    rerank_indices = fused_indices[
        :min(
            candidate_k,
            len(fused_indices)
        )
    ]

    rrf_time = (
        time.perf_counter() - start
    ) * 1000

    # ==============================================
    # 5. BGE RERANKING — HF ZEROGPU
    # ==============================================

    start = time.perf_counter()

    rerank_documents_list = [
        chunks[index]["text"]
        for index in rerank_indices
    ]

    # ---------- REQUEST ----------
    request_start = time.perf_counter()

    response = requests.post(
        f"{RERANKER_URL}/gradio_api/call/rerank",
        headers=HF_HEADERS,
        json={"data": [query, "\n\n".join(rerank_documents_list)]},
        timeout=60
    )

    request_time = (
        time.perf_counter() - request_start
    ) * 1000

    response.raise_for_status()

    event_id = response.json()["event_id"]

    # ---------- RESULT ----------
    result_start = time.perf_counter()

    result_response = requests.get(
        f"{RERANKER_URL}/gradio_api/call/rerank/{event_id}",
        headers=HF_HEADERS,
        timeout=60
    )

    result_time = (
        time.perf_counter() - result_start
    ) * 1000

    result_response.raise_for_status()

    # ---------- PARSE ----------
    rerank_results = None

    for line in result_response.text.splitlines():

        if line.startswith("data:"):

            data = json.loads(
                line[len("data:"):].strip()
            )

            rerank_results = data[0]
            break

    if rerank_results is None:
        raise RuntimeError(
            "HF reranker returned no results"
        )

    rerank_time = (
        time.perf_counter() - start
    ) * 1000

    # ==============================================
    # 6. SORT BY RERANK SCORE
    # ==============================================

    start = time.perf_counter()

    ranked_results = sorted(
        [
            (
                rerank_indices[item["index"]],
                item["score"]
            )
            for item in rerank_results
        ],
        key=lambda x: x[1],
        reverse=True
    )

    top_results = ranked_results[:k]

    sort_time = (
        time.perf_counter() - start
    ) * 1000

    # ==============================================
    # 7. BUILD RESULTS
    # ==============================================

    results = [
        {
            "text": chunks[index]["text"],
            "excerpt": get_relevant_excerpt(
                query,
                chunks[index]["text"]
            ),
            "page": chunks[index]["page"],
            "rerank_score": float(score)
        }
        for index, score in top_results
    ]

    total_time = (
        time.perf_counter() - total_start
    ) * 1000

    # ==============================================
    # RETRIEVAL PERFORMANCE
    # ==============================================

    print("\n===== RETRIEVAL BREAKDOWN =====")
    print(f"Embedding:       {embedding_time:.2f} ms")
    print(f"Dense search:    {dense_time:.2f} ms")
    print(f"BM25:            {bm25_time:.2f} ms")
    print(f"RRF:             {rrf_time:.2f} ms")
    print(f"BGE reranker:    {rerank_time:.2f} ms")
    print(f"Sorting:         {sort_time:.2f} ms")
    print(f"TOTAL:           {total_time:.2f} ms")
    print("===============================\n")

    print(f"HF POST:         {request_time:.2f} ms")
    print(f"HF GET/result:   {result_time:.2f} ms")
    print(f"HF TOTAL:        {rerank_time:.2f} ms")

    return results