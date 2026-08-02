# tests/test_rag.py

import sys
sys.path.append(".")

from agents.doc_ingestion import DocIngestionAgent
from pipelines.rag_pipeline import HermesRAGPipeline

# ═══════════════════════════════════════
# SETUP
# ═══════════════════════════════════════

print("Setting up pipeline...\n")

ingestion = DocIngestionAgent()
rag = HermesRAGPipeline()

doc = ingestion.ingest(
    "https://petstore.swagger.io/v2/swagger.json"
)
rag.build(doc)

# ═══════════════════════════════════════
# TEST 1: Basic question
# ═══════════════════════════════════════

print("=" * 50)
print("TEST 1: Basic Question")
print("=" * 50)

result = rag.query("What endpoints are available?")

print(f"\nAnswer:\n{result['answer'][:400]}...")
print(f"\nSources: {[s for s in result['sources']]}")
print(f"Confidence: {result['confidence']}")

# def get_relevant_chunks(self, query, n=3):
#     raise NotImplementedError

# def get_relevant_chunks(self, query, n=3):
#     raise NotImplementedError

print(f"Chunks used: {result['chunks_used']}")

# ═══════════════════════════════════════
# TEST 2: Section filtered question
# ═══════════════════════════════════════

print("\n" + "=" * 50)
print("TEST 2: Section Filtered Query")
print("=" * 50)

result2 = rag.query(
    "How does authentication work?",
    section_filter="authentication"
    # Sirf authentication section se answer lo
    # Agar section mein nahi hai → empty result
)

print(f"\nAnswer:\n{result2['answer'][:300]}...")
print(f"Section filter used: authentication only")

# ═══════════════════════════════════════
# TEST 3: Not in docs
# ═══════════════════════════════════════

print("\n" + "=" * 50)
print("TEST 3: Information Not In Docs")
print("=" * 50)

result3 = rag.query("What is the monthly pricing plan?")
print(f"\nAnswer: {result3['answer']}")
# Expected: Clearly says not found
# NOT a hallucinated price

# ═══════════════════════════════════════
# TEST 4: Raw chunks
# ═══════════════════════════════════════

print("\n" + "=" * 50)
print("TEST 4: Raw Chunks (for other agents)")
print("=" * 50)

chunks = rag.get_relevant_chunks(
    question="POST endpoint create add new",
    n=3
)

print(f"\nFound {len(chunks)} relevant chunks:")
for i, chunk in enumerate(chunks, 1):
    print(f"\n  Chunk {i} [{chunk['section']}]:")
    print(f"  {chunk['text'][:150]}...")

# ═══════════════════════════════════════
# TEST 5: Speed test
# ═══════════════════════════════════════

print("\n" + "=" * 50)
print("TEST 5: Query Speed")
print("=" * 50)

import time
start = time.time()
rag.query("What parameters does POST /pet require?")
elapsed = time.time() - start

print(f"\nQuery time: {elapsed:.2f} seconds")
print("(Should be under 3 seconds)")

print("\n✅ All RAG tests done!")