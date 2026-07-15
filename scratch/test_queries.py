# File: scratch/test_queries.py
import urllib.request
import json

queries = [
    "Why does Python asyncio use coroutines instead of OS-level threads?",
    "Why is cosine similarity recommended for 1024-dim BAAI/bge vector embeddings in Pinecone?",
    "How do GraphRAG traversals in Neo4j complement vector similarity search?"
]

url = "http://127.0.0.1:8000/api/v1/retrieval/search"

for q in queries:
    print("=" * 65)
    print(f"QUERY: {q}")
    req = urllib.request.Request(
        url,
        data=json.dumps({"query": q, "top_k": 3}).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        for i, c in enumerate(data["data"]["retrieved_chunks"]):
            print(f"  Rank #{i+1} -> [{c['document_id']}] (Score: {c['score']:.6f})")
