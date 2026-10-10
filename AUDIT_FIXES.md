# Bounded retries and a pipeline slice

Repair branch: `fix/internship-audit-20261010`. Changes are scoped to audit findings; no deployment or live provider action is included.

## Changed

Provider retries are bounded with per-call timeout and no unbounded recursive cycling. Unused provider constructors no longer require irrelevant credentials. Added an offline OpenAPI → schema → dependency ordering → generated-code compilation test using an explicitly stubbed model boundary.

## Verification

`pytest -q`

Commands are entry points, not a claim that every live integration was executed. See the repair bundle for actual results.

## Setup and remaining evidence

Install application dependencies from the actual project requirement files; run the Socket.IO ASGI socket_app in app.py. The orchestrator is pipelines/orchestrator.py. Offline compilation proves the wiring for a fixture, not live model correctness or generated-code safety. Authenticated user isolation, untrusted URL ingestion, generated-code sandboxing, a labelled endpoint corpus and live provider integration remain open. Use trusted local documents and manually review generated code; do not expose this prototype publicly.
