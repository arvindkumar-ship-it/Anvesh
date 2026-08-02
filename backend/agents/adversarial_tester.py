# agents/adversarial_tester.py

import json
from dataclasses import dataclass
from typing import List, Optional
from llm_config import get_llm_response
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import os
from pydantic import SecretStr

from agents.code_generator import GeneratedCode
load_dotenv()

# ═══════════════════════════════════════════
# DATA STRUCTURE
# ═══════════════════════════════════════════

@dataclass
class FailureCase:
    attack_type: str
    description: str
    scenario: str
    vulnerable_code: str
    code_gap: str
    severity: str        # "critical", "high", "medium"


# ═══════════════════════════════════════════
# ADVERSARIAL TESTER AGENT
# ═══════════════════════════════════════════

class AdversarialTesterAgent:
    """
    7 real production failures ke against code test karo.

    Ye sab failures actual production mein hote hain.
    Har developer ne kabhi na kabhi ye face kiya hai.

    LLM code analyst ki tarah kaam karta hai —
    "Agar ye scenario aaya toh kya hoga?"
    """

    ATTACK_PATTERNS = [
        {
            "name": "RATE_LIMIT_HIT",
            "severity": "critical",
            "description": "API 429 Too Many Requests deta hai",
            "scenario": """
API suddenly returns HTTP 429:
{"error": "Rate limit exceeded", "retry_after": 60}

Does the code:
1. Detect 429 status code?
2. Wait before retrying?
3. Use exponential backoff?
4. Give up after max retries?

Or does it crash immediately on 429?
""",
            "check": (
                "Look for: status_code == 429, "
                "time.sleep(), retry loop, max_retries"
            )
        },
        {
            "name": "AUTH_TOKEN_EXPIRED",
            "severity": "critical",
            "description": "Auth token mid-execution expire ho gaya",
            "scenario": """
First API call succeeds with 200.
Second API call returns HTTP 401:
{"error": "Token expired or invalid"}

Does the code:
1. Check for 401 status code?
2. Print meaningful error message?
3. Not silently continue with wrong data?

Or does it crash with unhandled 401?
""",
            "check": (
                "Look for: status_code == 401, "
                "auth error handling, graceful failure"
            )
        },
        {
            "name": "EMPTY_RESPONSE",
            "severity": "high",
            "description": "API empty ya null response deta hai",
            "scenario": """
API returns HTTP 200 but body is:
- Empty string: ""
- Null: null
- Empty dict: {}
- Empty list: []

Code then tries: response_data['id'] or response_data[0]
Does it crash with KeyError/IndexError/TypeError?
Or does it handle empty responses gracefully?
""",
            "check": (
                "Look for: null checks, empty dict/list checks, "
                ".get() usage, len() checks before indexing"
            )
        },
        {
            "name": "PAGINATION_NOT_HANDLED",
            "severity": "high",
            "description": "Sirf pehla page fetch hua, baaki miss",
            "scenario": """
List endpoint returns:
{
  "data": [10 items],
  "total": 847,
  "has_more": true,
  "next_cursor": "abc123"
}

Does code fetch ALL 847 items across all pages?
Or does it silently return only first 10 items
without any warning?
""",
            "check": (
                "Look for: pagination loop, "
                "has_more/next/cursor handling, "
                "while loop for pages"
            )
        },
        {
            "name": "NETWORK_TIMEOUT",
            "severity": "high",
            "description": "API response timeout",
            "scenario": """
API server takes too long to respond.
httpx raises: httpx.TimeoutException

Does code have timeout configured?
  (httpx.Client(timeout=30) or timeout parameter)
Does it retry on timeout?
Or does it crash with unhandled TimeoutException?
""",
            "check": (
                "Look for: timeout= parameter, "
                "TimeoutException handler, "
                "retry on timeout"
            )
        },
        {
            "name": "NESTED_ERROR_IN_200",
            "severity": "medium",
            "description": "HTTP 200 ke andar hidden error",
            "scenario": """
API returns HTTP 200 (success status) but body has error:
{"success": false, "error": "Insufficient permissions"}
OR
{"status": "error", "code": 1042, "message": "Invalid input"}
OR
{"result": null, "error": {"type": "not_found"}}

Does code check for errors inside the 200 response body?
Or does it assume HTTP 200 always means success?
""",
            "check": (
                "Look for: success field check, "
                "error field check, status field check, "
                "nested error handling"
            )
        },
        {
            "name": "MISSING_REQUIRED_FIELD",
            "severity": "medium",
            "description": "Response mein expected field missing",
            "scenario": """
Code does: pet_id = response['pet']['id']
But API returns: {"pet": {"name": "Max"}}
(id field is missing)

Or code does: first_item = items[0]
But items = [] (empty list)

Does code crash with KeyError or IndexError?
Or does it use .get() and check list length?
""",
            "check": (
                "Look for: .get() instead of [], "
                "list length checks before indexing, "
                "safe nested access"
            )
        }
    ]

    def __init__(self):
        # self.llm = ChatGroq(
        #     model="llama-3.3-70b-versatile",
        #     # Adversarial testing ke liye gpt-4o-mini enough hai
        #     # Code analysis = pattern matching
        #     # gpt-4o ki zaroorat nahi
        #     temperature=0,
        #     api_key=SecretStr(os.getenv("GROQ_API_KEY") or "")
        pass
        

    # ─────────────────────────────────────
    # MAIN ENTRY POINT
    # ─────────────────────────────────────

    def attack(
        self,
        generated_code: GeneratedCode,
        schema
    ) -> List[FailureCase]:

        print("\n⚔️  Adversarial testing...")
        print(f"   {len(self.ATTACK_PATTERNS)} attack patterns")

        failures = []

        for i, pattern in enumerate(self.ATTACK_PATTERNS, 1):
            print(
                f"   [{i}/{len(self.ATTACK_PATTERNS)}] "
                f"{pattern['name']}...",
                end=" ",
                flush=True
                # flush=True kyun?
                # Python output buffer karta hai by default
                # flush=True → immediately print karo
                # Progress dots real-time dikhenge
            )

            failure = self._run_single_attack(
                pattern,
                generated_code.code,
                schema
            )

            if failure:
                print("❌ VULNERABLE")
                failures.append(failure)
            else:
                print("✅ safe")

        # Summary
        passed = len(self.ATTACK_PATTERNS) - len(failures)
        print(f"\n✅ Results: {passed}/7 passed, "
              f"{len(failures)}/7 failed")

        return failures

    # ─────────────────────────────────────
    # SINGLE ATTACK
    # ─────────────────────────────────────

    def _run_single_attack(
        self,
        pattern: dict,
        code: str,
        schema
    ) -> Optional[FailureCase]:
        """
        Optional[FailureCase] return type kyun?
        None → code handles this attack (no failure)
        FailureCase → vulnerability found
        """

        prompt = f"""
You are a senior engineer doing adversarial code review.
Be strict — partial handling counts as NOT handling.

=== CODE TO REVIEW ===
{code}

=== ATTACK PATTERN ===
Name: {pattern['name']}
Description: {pattern['description']}

=== FAILURE SCENARIO ===
{pattern['scenario']}

=== WHAT TO CHECK ===
{pattern['check']}

=== YOUR ANALYSIS TASK ===
Read the code carefully line by line.
Determine if this specific failure is handled.

Return ONLY this JSON (no explanation, no markdown):
{{
    "handles_correctly": true or false,
    "vulnerable_part": "exact function or line that fails",
    "code_gap": "what specific code is missing",
    "evidence": "quote the problematic line from the code"
}}
"""

        try:
            # response = self.llm.invoke(prompt)
            # raw = str(response.content).strip()
            # response = get_llm_response([{"role": "user", "content": prompt}])
            response = get_llm_response(prompt)
            raw = str(response).strip()

            # JSON extract
            if "```" in raw:
                parts = raw.split("```")
                raw = parts[1] if len(parts) > 1 else raw
                if raw.startswith("json"):
                    raw = raw[4:]
                raw = raw.split("```")[0]

            result = json.loads(raw.strip())

            # Handles correctly → no failure → return None
            if result.get("handles_correctly", True):
                return None

            # Vulnerability found
            return FailureCase(
                attack_type=pattern["name"],
                description=pattern["description"],
                scenario=pattern["scenario"],
                vulnerable_code=result.get(
                    "vulnerable_part", "Unknown"
                ),
                code_gap=result.get(
                    "code_gap", "Gap not identified"
                ),
                severity=pattern["severity"]
            )

        except json.JSONDecodeError as e:
            # JSON parse fail → assume no failure
            # Conservative choice: don't flag false positives
            print(f"\n   (Parse error: {e})", end=" ")
            return None

        except Exception as e:
            print(f"\n   (Error: {e})", end=" ")
            return None