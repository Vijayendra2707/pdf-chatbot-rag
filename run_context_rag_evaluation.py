import json
import time
import uuid
import requests
from statistics import median

API_URL = "http://127.0.0.1:8000"
INPUT_FILE = "context_rag_30_qa_evaluation.json"
OUTPUT_FILE = "context_rag_results.json"

with open(INPUT_FILE, "r", encoding="utf-8") as f:
    questions = json.load(f)

results = []

print(f"Running {len(questions)} evaluation questions...\n")

for i, item in enumerate(questions, 1):
    question = item["question"]

    # Fresh session per question so previous evaluation answers
    # do not contaminate router/memory behavior.
    session_id = str(uuid.uuid4())

    payload = {
        "question": question,
        "session_id": session_id
    }

    print(f"[{i:02d}/30] {question}")

    start = time.perf_counter()

    try:
        response = requests.post(
            f"{API_URL}/ask",
            json=payload,
            timeout=120
        )

        elapsed_ms = (time.perf_counter() - start) * 1000

        response.raise_for_status()
        data = response.json()

        # Keep the complete API response so no evaluation information
        # is lost even if your response schema changes.
        result = {
            "id": item["id"],
            "question": question,
            "expected_answer": item["expected_answer"],
            "category": item["category"],
            "session_id": session_id,
            "client_total_latency_ms": round(elapsed_ms, 2),
            "api_response": data
        }

        # Convenience fields for common ContextRAG response formats.
        if isinstance(data, dict):
            result["answer"] = data.get("answer", data.get("response", ""))
            result["route"] = data.get("route", "")
            result["metrics"] = data.get("metrics", {})
            result["sources"] = data.get(
                "sources",
                data.get("source", [])
            )

        results.append(result)

        preview = result.get("answer", "")
        if isinstance(preview, str):
            preview = preview.replace("\n", " ")[:140]

        print(f"       latency: {elapsed_ms:.0f} ms")
        print(f"       answer:  {preview}")
        print()

    except Exception as e:
        elapsed_ms = (time.perf_counter() - start) * 1000

        results.append({
            "id": item["id"],
            "question": question,
            "expected_answer": item["expected_answer"],
            "category": item["category"],
            "session_id": session_id,
            "client_total_latency_ms": round(elapsed_ms, 2),
            "error": str(e)
        })

        print(f"       ERROR: {e}\n")

    # Small pause to avoid hammering the local API/HF ZeroGPU.
    time.sleep(0.5)

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2, ensure_ascii=False)

successful = [
    r for r in results
    if "error" not in r
]

latencies = [
    r["client_total_latency_ms"]
    for r in successful
]

print("=" * 60)
print("EVALUATION COMPLETE")
print("=" * 60)
print(f"Questions:       {len(results)}")
print(f"Successful:      {len(successful)}")
print(f"Failed:          {len(results) - len(successful)}")

if latencies:
    print(f"Median latency:  {median(latencies):.2f} ms")
    print(f"Average latency: {sum(latencies)/len(latencies):.2f} ms")
    print(f"Min latency:     {min(latencies):.2f} ms")
    print(f"Max latency:     {max(latencies):.2f} ms")

print(f"\nSaved results to: {OUTPUT_FILE}")