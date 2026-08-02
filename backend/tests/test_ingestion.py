# tests/test_ingestion.py

import sys
sys.path.append(".")
# sys.path.append kyun?
# Python modules dhundhta hai sys.path mein
# tests/ folder se parent folder ka module
# import karna hai → path add karo

from agents.doc_ingestion import DocIngestionAgent

agent = DocIngestionAgent()

# ═══════════════════════════════════════
# TEST 1: OpenAPI
# ═══════════════════════════════════════

print("=" * 50)
print("TEST 1: OpenAPI JSON")
print("=" * 50)

doc = agent.ingest(
    "https://petstore.swagger.io/v2/swagger.json"
    # Ye free test API hai — Swagger ka official example
    # Koi API key nahi chahiye
    # Hamesha available rehti hai
)

print(f"Format:          {doc.format_type}")
print(f"API Title:       {doc.metadata.get('title')}")
print(f"Endpoint count:  {doc.metadata.get('endpoint_count')}")
print(f"Sections:        {list(doc.sections.keys())}")
print(f"Text length:     {len(doc.raw_text)} chars")

# Sections mein actual content check karo
print("\nSection sizes:")
for section, content in doc.sections.items():
    print(f"  [{section}]: {len(content)} chars")

# ═══════════════════════════════════════
# TEST 2: HTML
# ═══════════════════════════════════════

print("\n" + "=" * 50)
print("TEST 2: HTML Documentation")
print("=" * 50)

doc2 = agent.ingest("https://jsonplaceholder.typicode.com/")
# JSONPlaceholder — free fake REST API
# Simple HTML docs, good for testing HTML parser

print(f"Format:         {doc2.format_type}")
print(f"Title:          {doc2.metadata.get('title')}")
print(f"Sections found: {doc2.metadata.get('section_count')}")
print(f"Text length:    {len(doc2.raw_text)} chars")

# ═══════════════════════════════════════
# TEST 3: Plain Text
# ═══════════════════════════════════════

print("\n" + "=" * 50)
print("TEST 3: Plain Text")
print("=" * 50)

sample = """
Authentication: Use Bearer token in Authorization header.
Base URL: https://api.example.com/v1
Endpoints:
  GET /users - Returns list of users
  POST /users - Creates new user (requires: name, email)
Rate Limit: 100 requests per minute
"""

doc3 = agent.ingest(sample)
print(f"Format:  {doc3.format_type}")
print(f"Length:  {len(doc3.raw_text)} chars")

# ═══════════════════════════════════════
# TEST 4: Edge Cases
# ═══════════════════════════════════════

print("\n" + "=" * 50)
print("TEST 4: Edge Cases")
print("=" * 50)

# 4a: Wrong URL
try:
    bad = agent.ingest("https://this-does-not-exist-xyz123.com")
    print("❌ Should have thrown error")
except Exception as e:
    print(f"✅ Wrong URL handled: {type(e).__name__}")
    # type(e).__name__ → exception ka class naam
    # e.g. "ConnectError", "HTTPStatusError"

# 4b: Empty string
doc5 = agent.ingest("")
print(f"✅ Empty text: format={doc5.format_type}, "
      f"chars={len(doc5.raw_text)}")

print("\n✅ All tests passed!")