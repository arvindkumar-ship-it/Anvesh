import sys
sys.path.append(".")

from pipelines.orchestrator import HermesOrchestrator

print("=" * 60)
print("HERMES — Complete End-to-End Test")
print("=" * 60)

orchestrator = HermesOrchestrator()

result = orchestrator.run(
    source_url=(
        "https://petstore.swagger.io/v2/swagger.json"
    ),
    user_task=(
        "Add a new pet named 'Bruno' with status 'available', "
        "then find all available pets, "
        "then fetch Bruno by ID to verify creation"
    )
)

if result["success"]:
    r = result["results"]

    print("\n✅ PIPELINE COMPLETE\n")
    print(f"API:           {r['schema'].api_name}")
    print(f"Endpoints:     {r['schema'].total_endpoints}")
    print(f"Gaps:          {len(r['ambiguities'])}")
    print(f"Dep steps:     {len(r['dep_map'].execution_order)}")
    print(f"Attacks fixed: {len(r['failures'])}")

    draft_lines  = len(r['generated'].code.splitlines())
    final_lines  = len(r['hardened_code'].splitlines())
    print(f"Code:          {draft_lines} → {final_lines} lines")

    # Q&A results
    print("\nAuto Q&A Results:")
    for topic, qa in r['qa_results'].items():
        conf = qa.confidence
        emoji = {"high":"✅","medium":"🟡","low":"❓","none":"❌"}.get(
            conf, "❓"
        )
        print(f"  {emoji} {topic}: {qa.answer[:80]}...")

    # Save outputs
    with open("final_report.md", encoding="utf-8", mode="w") as f:
        f.write(r["report"])
    print(f"\n📄 Report saved: final_report.md")

    with open("final_code.py", encoding="utf-8", mode="w") as f:
        f.write(r["hardened_code"])
    print(f"💻 Code saved:  final_code.py")

    print(f"\n→ Open final_report.md to see full analysis")
    print(f"→ Open final_code.py to see production code")

else:
    print(f"\n❌ Failed: {result['error']}")
