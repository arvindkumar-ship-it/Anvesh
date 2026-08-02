# tests/test_analysis.py

import sys
print("START", flush=True)
sys.stdout.flush()
sys.path.append(".")

from collections import Counter

from agents.doc_ingestion import DocIngestionAgent
from pipelines.rag_pipeline import HermesRAGPipeline
from agents.schema_extractor import SchemaExtractorAgent
from agents.ambiguity_detector import AmbiguityDetectorAgent
from agents.dependency_mapper import DependencyMapperAgent

# ═══════════════════════════════════════
# SETUP
# ═══════════════════════════════════════

print("Setting up pipeline...\n")

ingestion     = DocIngestionAgent()
rag           = HermesRAGPipeline()
schema_agent  = SchemaExtractorAgent(rag)
ambiguity_agent  = AmbiguityDetectorAgent(rag)
dependency_agent = DependencyMapperAgent(rag)

doc    = ingestion.ingest("https://petstore.swagger.io/v2/swagger.json")
rag.build(doc)
schema = schema_agent.extract(doc)

# ═══════════════════════════════════════
# TEST 1: Ambiguity Detection
# ═══════════════════════════════════════

print("=" * 50)
print("TEST 1: Ambiguity Detection")
print("=" * 50)

ambiguities = ambiguity_agent.detect(schema)

print(f"\nTotal: {len(ambiguities)}")

# Counter se type breakdown
type_counts = Counter(a.ambiguity_type for a in ambiguities)
print("\nBy type:")
for amb_type, count in type_counts.most_common():
    print(f"  {amb_type}: {count}")

# High severity detail
high = [a for a in ambiguities if a.severity == "high"]
print(f"\n🔴 High severity ({len(high)}):")
for a in high[:3]:
    print(f"\n  Endpoint:   {a.endpoint}")
    print(f"  Issue:      {a.description}")
    print(f"  Assumption: {a.assumption_made}")

# Summary test
print("\nSummary (first 2 items):")
print(ambiguity_agent.get_summary(ambiguities[:2]))

# ═══════════════════════════════════════
# TEST 2: Dependency Mapping
# ═══════════════════════════════════════

print("=" * 50)
print("TEST 2: Dependency Mapping")
print("=" * 50)

dep_map = dependency_agent.map(schema)

print(f"\nExecution order ({len(dep_map.execution_order)} steps):")
for i, path in enumerate(dep_map.execution_order, 1):
    deps = dep_map.dependencies.get(path, [])
    dep_str = f" ← needs: {deps[0]}" if deps else " (independent)"
    print(f"  {i}. {path}{dep_str}")

print(f"\nCircular dependency: {dep_map.has_circular}")
print(f"Independent endpoints: {len(dep_map.independent_endpoints)}")

if dep_map.dependency_details:
    print(f"\nDependency details (first 3):")
    for dep in dep_map.dependency_details[:3]:
        print(f"\n  {dep.endpoint}")
        print(f"  → depends on: {dep.depends_on}")
        print(f"  → reason: {dep.reason}")

# ═══════════════════════════════════════
# TEST 3: Handoff Check
# ═══════════════════════════════════════

print("\n" + "=" * 50)
print("TEST 3: Ready for Code Generator?")
print("=" * 50)

print(f"\n✅ Schema:       {len(schema.endpoints)} endpoints")
print(f"✅ Ambiguities:  {len(ambiguities)} found")
print(f"✅ Exec order:   {len(dep_map.execution_order)} steps")

print(f"\n→ Code generator input ready:")
print(f"  code_agent.generate(schema, dep_map, ambiguities, task)")

print("\n✅ All tests done!")