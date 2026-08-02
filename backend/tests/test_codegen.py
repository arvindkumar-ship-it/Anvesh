

import sys
sys.path.append(".")

from agents.doc_ingestion import DocIngestionAgent
from pipelines.rag_pipeline import HermesRAGPipeline
from agents.schema_extractor import SchemaExtractorAgent
from agents.ambiguity_detector import AmbiguityDetectorAgent
from agents.dependency_mapper import DependencyMapperAgent
from agents.code_generator import CodeGeneratorAgent
from agents.adversarial_tester import AdversarialTesterAgent
from agents.code_hardener import CodeHardenerAgent

# ═══════════════════════════════════════
# SETUP
# ═══════════════════════════════════════

print("=" * 60)
print("HERMES — Feature 5 Complete Test")
print("=" * 60)

# Feature 1-4 setup
ingestion        = DocIngestionAgent()
rag              = HermesRAGPipeline()
schema_agent     = SchemaExtractorAgent(rag)
ambiguity_agent  = AmbiguityDetectorAgent(rag)
dependency_agent = DependencyMapperAgent(rag)

# Feature 5 agents
code_agent    = CodeGeneratorAgent()
attack_agent  = AdversarialTesterAgent()
hardener      = CodeHardenerAgent()

# Pipeline chalao
print("\n[1/7] Ingesting...")
doc = ingestion.ingest(
    "https://petstore.swagger.io/v2/swagger.json"
)

print("\n[2/7] Building RAG...")
rag.build(doc)

print("\n[3/7] Extracting schema...")
schema = schema_agent.extract(doc)

print("\n[4/7] Detecting ambiguities...")
ambiguities = ambiguity_agent.detect(schema)

print("\n[5/7] Mapping dependencies...")
dep_map = dependency_agent.map(schema)

# ═══════════════════════════════════════
# TEST 1: Code Generation
# ═══════════════════════════════════════

print("\n" + "=" * 50)
print("TEST 1: Code Generation")
print("=" * 50)

user_task = (
    "Add a new pet named 'Bruno' with status 'available', "
    "then fetch it by ID to verify it was created"
)

print(f"\n[6/7] Generating for task:")
print(f"      '{user_task}'")

generated = code_agent.generate(
    schema=schema,
    dep_map=dep_map,
    ambiguities=ambiguities,
    user_task=user_task
)

# Code preview
lines = generated.code.splitlines()
print(f"\nGenerated code ({len(lines)} lines):")
print("-" * 40)
for i, line in enumerate(lines[:25], 1):
    print(f"{i:3}  {line}")
if len(lines) > 25:
    print(f"     ... {len(lines)-25} more lines")

print(f"\nEndpoints used: {generated.endpoints_used}")
print(f"Assumptions:    {len(generated.assumptions)}")

# ═══════════════════════════════════════
# TEST 2: Adversarial Testing
# ═══════════════════════════════════════

print("\n" + "=" * 50)
print("TEST 2: Adversarial Testing")
print("=" * 50)

failures = attack_agent.attack(generated, schema)

print(f"\nSummary:")
print(f"  Passed: {7-len(failures)}/7")
print(f"  Failed: {len(failures)}/7")

if failures:
    print(f"\nFailures detail:")
    for f in failures:
        emoji = {"critical":"🔴","high":"🟠","medium":"🟡"}.get(
            f.severity, "⚪"
        )
        print(f"\n  {emoji} {f.attack_type} [{f.severity}]")
        print(f"     Gap: {f.code_gap[:80]}")

# ═══════════════════════════════════════
# TEST 3: Code Hardening
# ═══════════════════════════════════════

print("\n" + "=" * 50)
print("TEST 3: Code Hardening")
print("=" * 50)

print(f"\n[7/7] Hardening code...")
hardened = hardener.harden(generated, failures)

# Hardened code preview
hardened_lines = hardened.splitlines()
print(f"\nHardened code ({len(hardened_lines)} lines):")
print("-" * 40)
for i, line in enumerate(hardened_lines[:30], 1):
    print(f"{i:3}  {line}")
if len(hardened_lines) > 30:
    print(f"     ... {len(hardened_lines)-30} more lines")

# ═══════════════════════════════════════
# TEST 4: Save Output
# ═══════════════════════════════════════

print("\n" + "=" * 50)
print("TEST 4: Save Output")
print("=" * 50)

with open("output_generated.py", "w") as f:
    f.write(hardened)
    # "w" mode = write mode
    # File exist kare toh overwrite
    # Exist na kare toh create
    # "a" = append mode hota (add to end)

print(f"\n✅ Saved to: output_generated.py")
print(f"   Open it and read — should be complete!")

# ═══════════════════════════════════════
# FINAL SUMMARY
# ═══════════════════════════════════════

print("\n" + "=" * 60)
print("FEATURE 5 COMPLETE — Summary")
print("=" * 60)

print(f"""
✅ API:            {schema.api_name}
✅ Endpoints:      {len(schema.endpoints)} found
✅ Ambiguities:    {len(ambiguities)} detected
✅ Exec order:     {len(dep_map.execution_order)} steps
✅ Code (draft):   {len(lines)} lines
✅ Attacks passed: {7-len(failures)}/7
✅ Fixes applied:  {len(failures)}
✅ Code (final):   {len(hardened_lines)} lines

Output: output_generated.py
""")