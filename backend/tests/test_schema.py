# tests/test_schema.py

import sys
sys.path.append(".")

from agents.doc_ingestion import DocIngestionAgent
from pipelines.rag_pipeline import HermesRAGPipeline
from agents.schema_extractor import SchemaExtractorAgent

# ═══════════════════════════════════════
# SETUP
# ═══════════════════════════════════════

ingestion = DocIngestionAgent()
rag = HermesRAGPipeline()
schema_agent = SchemaExtractorAgent(rag)

# ═══════════════════════════════════════
# TEST 1: OpenAPI Direct Parse
# ═══════════════════════════════════════

print("=" * 50)
print("TEST 1: OpenAPI Schema Extraction")
print("=" * 50)

doc = ingestion.ingest(
    "https://petstore.swagger.io/v2/swagger.json"
)
rag.build(doc)
schema = schema_agent.extract(doc)

print(f"\n{schema.summary()}")

print(f"\nFirst 3 endpoints detail:")
for ep in schema.endpoints[:3]:
    print(f"\n  {ep.method} {ep.path}")
    print(f"  Description:  {ep.description}")
    print(f"  Required:     {ep.required_params}")
    print(f"  Optional:     {ep.optional_params}")
    print(f"  Param types:  {ep.param_types}")
    print(f"  Auth:         {ep.auth_required}")
    print(f"  Error codes:  {ep.error_codes[:2]}")

# ═══════════════════════════════════════
# TEST 2: Pydantic Validation
# ═══════════════════════════════════════

print("\n" + "=" * 50)
print("TEST 2: Schema Validation")
print("=" * 50)

# Sab endpoints valid hain?
invalid = []
for ep in schema.endpoints:
    if not ep.method:
        invalid.append(f"{ep.path}: missing method")
    if not ep.path:
        invalid.append(f"{ep.method}: missing path")
    if ep.method not in ["GET","POST","PUT","DELETE","PATCH","HEAD"]:
        invalid.append(f"{ep.path}: invalid method '{ep.method}'")

if invalid:
    print(f"❌ Issues: {invalid}")
else:
    print(f"✅ All {len(schema.endpoints)} endpoints valid")

# ═══════════════════════════════════════
# TEST 3: Serialization
# ═══════════════════════════════════════

print("\n" + "=" * 50)
print("TEST 3: Serialization (for other agents)")
print("=" * 50)

# model_dump() → dict
schema_dict = schema.model_dump()
print(f"Dict keys: {list(schema_dict.keys())}")

# model_dump_json() → JSON string
schema_json = schema.model_dump_json(indent=2)
print(f"JSON length: {len(schema_json)} chars")
print(f"First 200 chars of JSON:")
print(schema_json[:200])

# ═══════════════════════════════════════
# TEST 4: Auth Extraction
# ═══════════════════════════════════════

print("\n" + "=" * 50)
print("TEST 4: Auth Info")
print("=" * 50)

print(f"Auth method:       {schema.auth_method}")
print(f"Auth instructions: {schema.auth_instructions}")
print(f"Global headers:    {schema.global_headers}")

auth_endpoints = [
    ep for ep in schema.endpoints
    if ep.auth_required
]
# List comprehension with filter
# [item for item in list if condition]
print(f"Endpoints needing auth: {len(auth_endpoints)}")

# ═══════════════════════════════════════
# TEST 5: HTML Docs (LLM Strategy)
# ═══════════════════════════════════════

print("\n" + "=" * 50)
print("TEST 5: HTML Docs — LLM Strategy")
print("=" * 50)

doc2 = ingestion.ingest("https://jsonplaceholder.typicode.com/")
rag.build(doc2)
schema2 = schema_agent.extract(doc2)
# Ye LLM strategy use karega — format_type = "html"

print(f"\n{schema2.summary()}")
print(f"Endpoints found: {len(schema2.endpoints)}")

print("\n✅ All schema tests done!")