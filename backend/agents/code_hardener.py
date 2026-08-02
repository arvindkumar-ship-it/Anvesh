# agents/code_hardener.py

from dataclasses import dataclass
from typing import List

from typer import prompt
from llm_config import get_llm_response
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from agents.adversarial_tester import FailureCase
from agents.code_generator import GeneratedCode
import os

from pydantic import SecretStr

load_dotenv()

# ═══════════════════════════════════════════
# PRE-BUILT FIX TEMPLATES
# ═══════════════════════════════════════════
# Kyun templates? LLM se directly fix kyun nahi?
#
# Templates:
#   - Human-written → reliable
#   - Tested → works correctly
#   - Consistent style
#   - No extra API call
#
# LLM fix:
#   - Flexible → unknown failures ke liye
#   - Inconsistent kabhi kabhi
#   - Extra API call
#
# Strategy: Template available → template use karo
#           Template nahi → LLM use karo

FIX_TEMPLATES = {

    "RATE_LIMIT_HIT": '''
import time
from functools import wraps

def retry_on_rate_limit(
    max_retries: int = 3,
    backoff_factor: int = 2
):
    """
    Decorator: Automatically retry on rate limit (429).

    Exponential backoff kyun?
    Attempt 1: wait 2^1 = 2 seconds
    Attempt 2: wait 2^2 = 4 seconds
    Attempt 3: wait 2^3 = 8 seconds
    Server ko recover karne ka time milta hai
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                response = func(*args, **kwargs)

                if response.status_code == 429:
                    # Retry-After header check karo
                    retry_after = int(
                        response.headers.get(
                            "Retry-After",
                            backoff_factor ** (attempt + 1)
                        )
                    )
                    print(
                        f"Rate limited. "
                        f"Waiting {retry_after}s "
                        f"(attempt {attempt+1}/{max_retries})..."
                    )
                    time.sleep(retry_after)
                    continue

                return response

            raise Exception(
                f"Max retries ({max_retries}) exceeded. "
                f"Rate limit persists."
            )
        return wrapper
    return decorator
''',

    "AUTH_TOKEN_EXPIRED": '''
def handle_auth_error(
    response,
    endpoint: str = ""
) -> bool:
    """
    Check if response is 401 auth error.
    Returns True if auth failed (caller should stop).
    """
    if response.status_code == 401:
        error_data = {}
        try:
            error_data = response.json()
        except Exception:
            pass

        error_msg = (
            error_data.get("error")
            or error_data.get("message")
            or "Unauthorized"
        )
        print(f"Auth error at {endpoint}: {error_msg}")
        print("Check API key/token in .env file")
        return True  # Auth failed

    return False  # Auth OK
''',

    "EMPTY_RESPONSE": '''
def safe_parse_response(
    response,
    endpoint: str = ""
) -> dict | list | None:
    """
    Safely parse API response.
    Handles: empty body, null, non-JSON, empty dict/list.
    """
    # Empty body check
    if not response.content:
        print(f"Warning: Empty response body from {endpoint}")
        return None

    # JSON parse attempt
    try:
        data = response.json()
    except Exception:
        print(f"Warning: Non-JSON response from {endpoint}")
        print(f"Raw response: {response.text[:200]}")
        return None

    # Null check
    if data is None:
        print(f"Warning: Null response from {endpoint}")
        return None

    return data

def safe_get(
    data: dict | list | None,
    *keys,
    default=None
):
    """
    Safely access nested dict/list keys.

    Usage:
    safe_get(data, "user", "id")        # data["user"]["id"]
    safe_get(data, "items", 0, "name")  # data["items"][0]["name"]
    All with fallback to default instead of crash.
    """
    if data is None:
        return default

    try:
        result = data
        for key in keys:
            if result is None:
                return default
            elif isinstance(result, dict):
                result = result.get(key, default)
            elif isinstance(result, list):
                if not isinstance(key, int):
                    return default
                if not (-len(result) <= key < len(result)):
                    return default
                    # Bounds check kyun?
                    # result[5] when len(result)=3 → IndexError
                    # -len <= key < len → valid range
                result = result[key]
            else:
                return default
        return result
    except Exception:
        return default
''',

    "PAGINATION_NOT_HANDLED": '''
def fetch_all_pages(
    client,
    url: str,
    headers: dict,
    params: dict = {},
    data_key: str = "data",
    max_pages: int = 100
) -> list:
    """
    Fetch all pages from a paginated endpoint.

    Supports multiple pagination styles:
    - cursor-based: {"next_cursor": "abc123"}
    - page-based: {"page": 2, "has_more": true}
    - URL-based: {"next": "https://api.../page=2"}
    """
    all_items = []
    current_url = url
    page_num = 1

    while current_url and page_num <= max_pages:

        response = client.get(
            current_url,
            headers=headers,
            params=params if page_num == 1 else {}
            # First page pe params, baad mein URL handles it
        )
        response.raise_for_status()
        data = response.json()

        if isinstance(data, list):
            # Direct array response → no pagination
            all_items.extend(data)
            break

        elif isinstance(data, dict):
            # Extract items
            items = (
                data.get(data_key)
                or data.get("items")
                or data.get("results")
                or data.get("records")
                or []
            )
            all_items.extend(items)

            # Next page determine karo
            current_url = (
                data.get("next")
                or data.get("next_url")
                or data.get("next_page_url")
                or None
            )

            # Cursor-based pagination
            cursor = data.get("next_cursor") or data.get("cursor")
            if cursor and not current_url:
                params["cursor"] = cursor
                # URL same, cursor param update

            # has_more check
            has_more = data.get("has_more", False)
            if not has_more and not current_url and not cursor:
                break

        page_num += 1
        print(f"  Page {page_num-1} fetched, "
              f"total so far: {len(all_items)}")

    if page_num > max_pages:
        print(f"Warning: Stopped at {max_pages} pages limit")

    return all_items
''',

    "NETWORK_TIMEOUT": '''
import time

def make_request_with_retry(
    client,
    method: str,
    url: str,
    max_retries: int = 3,
    **kwargs
):
    """
    Make HTTP request with timeout retry.

    httpx.TimeoutException → wait → retry
    httpx.ConnectError → fail immediately (server unreachable)
    """
    import httpx

    for attempt in range(max_retries):
        try:
            response = client.request(method, url, **kwargs)
            return response

        except httpx.TimeoutException:
            wait = 2 ** attempt
            # Exponential: 1s, 2s, 4s
            print(
                f"Timeout on attempt {attempt+1}. "
                f"Waiting {wait}s..."
            )
            if attempt < max_retries - 1:
                time.sleep(wait)

        except httpx.ConnectError as e:
            print(f"Connection failed: {e}")
            print(f"Check URL: {url}")
            raise
            # raise kyun? re-raise original exception
            # ConnectError = server unreachable
            # Retry karne se kuch nahi hoga → fail fast

    raise httpx.TimeoutException(
        f"All {max_retries} attempts timed out for {url}"
    )
''',

    "NESTED_ERROR_IN_200": '''
def check_nested_errors(
    data: dict | list | None,
    endpoint: str = ""
) -> tuple[bool, str]:
    """
    Check if HTTP 200 response contains hidden errors.

    Returns: (has_error: bool, error_message: str)

    Common patterns:
    {"success": false, "message": "..."}
    {"status": "error", "error": "..."}
    {"error": {"code": 1042, "message": "..."}}
    """
    if data is None or not isinstance(data, dict):
        return False, ""

    # Pattern 1: success field
    if data.get("success") is False:
        msg = (
            data.get("message")
            or data.get("error")
            or "Request failed"
        )
        return True, str(msg)

    # Pattern 2: status field
    status = data.get("status", "")
    if str(status).lower() in ["error", "failed", "failure"]:
        msg = (
            data.get("message")
            or data.get("error")
            or f"Status: {status}"
        )
        return True, str(msg)

    # Pattern 3: error field exists and is truthy
    error_field = data.get("error")
    if error_field:
        if isinstance(error_field, dict):
            msg = error_field.get("message", str(error_field))
        else:
            msg = str(error_field)
        return True, msg

    # Pattern 4: code field indicating error (4xx range)
    code = data.get("code", 0)
    if isinstance(code, int) and 400 <= code < 600:
        msg = data.get("message", f"Error code: {code}")
        return True, msg

    return False, ""
''',

    "MISSING_REQUIRED_FIELD": '''
def safe_get(
    data: dict | list | None,
    *keys,
    default=None
):
    """
    Safely access nested dict/list without KeyError/IndexError.
    (Same as EMPTY_RESPONSE template — reuse)
    """
    if data is None:
        return default
    try:
        result = data
        for key in keys:
            if result is None:
                return default
            elif isinstance(result, dict):
                result = result.get(key, default)
            elif isinstance(result, list):
                if not isinstance(key, int):
                    return default
                if not (-len(result) <= key < len(result)):
                    return default
                result = result[key]
            else:
                return default
        return result
    except Exception:
        return default
'''
}


# ═══════════════════════════════════════════
# CODE HARDENER AGENT
# ═══════════════════════════════════════════

class CodeHardenerAgent:
    """
    Failures list → har ek fix karo.

    Priority order:
    1. Critical failures pehle
    2. Template available → template use karo
    3. Template nahi → LLM use karo
    4. Final polish pass
    """

    def __init__(self):
        # self.llm = ChatGroq(
        #     model="llama-3.3-70b-versatile",
        #     # Adversarial testing ke liye gpt-4o-mini enough hai
        #     # Code analysis = pattern matching
        #     # gpt-4o ki zaroorat nahi
        #     temperature=0,
        #     api_key=SecretStr(os.getenv("GROQ_API_KEY") or "")
        # )
        pass


    # ─────────────────────────────────────
    # MAIN ENTRY POINT
    # ─────────────────────────────────────

    def harden(
        self,
        generated_code: GeneratedCode,
        failures: List[FailureCase]
    ) -> str:

        print("\n🛡️  Hardening code...")

        if not failures:
            print("✅ No failures — code already solid!")
            return generated_code.code

        print(f"   Fixing {len(failures)} vulnerabilities...")

        # Critical pehle fix karo
        sorted_failures = sorted(
            failures,
            key=lambda f: {
                "critical": 0,
                "high": 1,
                "medium": 2
            }.get(f.severity, 3)
        )

        current_code = generated_code.code

        for i, failure in enumerate(sorted_failures, 1):
            print(
                f"   [{i}/{len(sorted_failures)}] "
                f"{failure.attack_type}...",
                end=" ",
                flush=True
            )

            fixed = self._fix_single_failure(
                current_code, failure
            )

            if fixed and fixed != current_code:
                current_code = fixed
                print("✅ fixed")
            else:
                print("⚠️  unchanged")

        # Final polish
        print("   Final polish...")
        current_code = self._final_polish(current_code)

        original_lines = len(generated_code.code.splitlines())
        final_lines = len(current_code.splitlines())

        print(f"\n✅ Hardening complete!")
        print(f"   {original_lines} → {final_lines} lines")

        return current_code

    # ─────────────────────────────────────
    # FIX SINGLE FAILURE
    # ─────────────────────────────────────

    def _fix_single_failure(
        self,
        code: str,
        failure: FailureCase
    ) -> str:

        template = FIX_TEMPLATES.get(failure.attack_type)

        if template:
            return self._apply_template_fix(
                code, failure, template
            )
        else:
            return self._apply_llm_fix(code, failure)

    # ─────────────────────────────────────
    # FIX METHOD 1: Template
    # ─────────────────────────────────────

    def _apply_template_fix(
        self,
        code: str,
        failure: FailureCase,
        template: str
    ) -> str:

        prompt = f"""
Fix a specific vulnerability in this Python code.

=== ORIGINAL CODE ===
{code}

=== VULNERABILITY ===
Type: {failure.attack_type}
Problem: {failure.code_gap}
Vulnerable part: {failure.vulnerable_code}

=== FIX TEMPLATE ===
Add this helper code and integrate it:
{template}

=== INSTRUCTIONS ===
1. Add the helper function(s) from template at top (after imports)
2. Find the vulnerable part in the code
3. Modify it to USE the helper function
4. Do NOT change any other logic
5. Return COMPLETE fixed Python code

Return ONLY Python code. No explanation. No markdown.
"""
        # response = self.llm.invoke(prompt)
        # response_text = get_llm_response([{"role": "user", "content": prompt}])
        response_text = get_llm_response(prompt)
        return self._extract_code(str(response_text))

    # ─────────────────────────────────────
    # FIX METHOD 2: LLM
    # ─────────────────────────────────────

    def _apply_llm_fix(
        self,
        code: str,
        failure: FailureCase
    ) -> str:

        prompt = f"""
Fix this specific vulnerability in Python code.

=== ORIGINAL CODE ===
{code}

=== VULNERABILITY ===
Attack type: {failure.attack_type}
Description: {failure.description}
What is missing: {failure.code_gap}
Vulnerable part: {failure.vulnerable_code}

=== INSTRUCTIONS ===
1. Fix ONLY this specific vulnerability
2. Use Python best practices
3. Keep all existing logic intact
4. Return COMPLETE fixed Python code

Return ONLY Python code. No explanation. No markdown.
"""
        # response = self.llm.invoke(prompt)
        # response_text = get_llm_response([{"role": "user", "content": prompt}])
        # List aur Dict ka kachra hata de, sirf 'prompt' variable bhej
        # response_text = get_llm_response(prompt)
        # Line 538
        response_text = get_llm_response(prompt)
        return self._extract_code(str(response_text))

    # ─────────────────────────────────────
    # FINAL POLISH
    # ─────────────────────────────────────

    def _final_polish(self, code: str) -> str:
        """
        Last cleanup pass.
        Multiple fixes ke baad:
        - Duplicate imports ho sakte hain
        - Duplicate function definitions ho sakti hain
        - Import order messy ho sakta hai
        """

        prompt = f"""
Do a final cleanup pass on this Python code.

=== CODE ===
{code}

=== CLEANUP TASKS ===
1. Move ALL imports to top of file
2. Remove duplicate import statements
3. Remove duplicate function definitions
   (keep the more complete version)
4. Ensure main() function exists and is complete
5. Ensure: if __name__ == '__main__': main() at bottom
6. Add load_dotenv() at start of main() if missing
7. Ensure httpx.Client has timeout:
   httpx.Client(timeout=httpx.Timeout(30.0))
8. Fix obvious syntax errors if any

Return ONLY cleaned Python code. No explanation. No markdown.
"""
        # response = self.llm.invoke(prompt)
        # response_text = get_llm_response([{"role": "user", "content": prompt}])
        response_text = get_llm_response(prompt)
        return self._extract_code(str(response_text))

    # ─────────────────────────────────────
    # HELPER: Code extract karo
    # ─────────────────────────────────────

    def _extract_code(self, raw: str) -> str:

        if "```python" in raw:
            start = raw.find("```python") + 9
            end = raw.find("```", start)
            if end > start:
                return raw[start:end].strip()

        elif "```" in raw:
            start = raw.find("```") + 3
            end = raw.find("```", start)
            if end > start:
                return raw[start:end].strip()

        return raw.strip()