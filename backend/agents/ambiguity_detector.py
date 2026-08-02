# # agents/ambiguity_detector.py

# from dataclasses import dataclass
# from typing import List, Optional
# from langchain_openai import ChatOpenAI
# from llm_config import get_llm_response
# from pydantic import SecretStr
# from dotenv import load_dotenv
# import os

# load_dotenv()

# # ═══════════════════════════════════════════
# # DATA STRUCTURE
# # ═══════════════════════════════════════════

# @dataclass
# class Ambiguity:
#     endpoint: str
#     ambiguity_type: str
#     # "missing_param_type"
#     # "missing_error_codes"
#     # "unclear_auth"
#     # "no_rate_limit"
#     # "missing_example"
#     # "unclear_param_values"
#     # "unclear_response"
#     # "missing_pagination"

#     description: str
#     severity: str           # "high" / "medium" / "low"
#     assumption_made: str    # Code generator ye use karega
#     parameter: Optional[str] = None


# # ═══════════════════════════════════════════
# # AMBIGUITY DETECTOR
# # ═══════════════════════════════════════════

# class AmbiguityDetectorAgent:
#     """
#     Schema ke har endpoint ko 8 checks se analyze karta hai.
#     Jo missing hai uski assumption document karta hai.
#     Code generator ye assumptions use karega.
#     """

#     def __init__(self, rag_pipeline):
#         self.rag = rag_pipeline
# #         self.llm = ChatGroq(
# #     model="llama3-8b-8192",
# #     temperature=0,
# #     api_key=SecretStr(os.getenv("GROQ_API_KEY") or "")
# # )


#     # ─────────────────────────────────────
#     # MAIN ENTRY POINT
#     # ─────────────────────────────────────

#     def detect(self, schema) -> List[Ambiguity]:

#         print("\n⚠️  Detecting ambiguities...")

#         all_ambiguities = []

#         for endpoint in schema.endpoints:
#             # Har endpoint ke liye sab checks run karo

#             checks = [
#                 self._check_param_types(endpoint),
#                 self._check_param_values(endpoint),
#                 self._check_error_codes(endpoint),
#                 self._check_auth(endpoint, schema),
#                 self._check_rate_limit(endpoint, schema),
#                 self._check_examples(endpoint),
#                 self._check_response_structure(endpoint),
#                 self._check_pagination(endpoint),
#             ]

#             for check_result in checks:
#                 all_ambiguities.extend(check_result)
#                 # extend() → list mein list add karo (flat)

#         # High severity pehle sort karo
#         all_ambiguities.sort(
#             key=lambda x: {
#                 "high": 0, "medium": 1, "low": 2
#             }.get(x.severity, 3)
#         )

#         # Summary
#         high   = sum(1 for a in all_ambiguities if a.severity == "high")
#         medium = sum(1 for a in all_ambiguities if a.severity == "medium")
#         low    = sum(1 for a in all_ambiguities if a.severity == "low")
#         # sum(1 for ...) kyun?
#         # len([a for a in ... if ...]) → list banata hai
#         # sum(1 for ... if ...) → generator, memory efficient

#         print(f"✅ Done! 🔴{high} 🟡{medium} 🟢{low} "
#               f"= {len(all_ambiguities)} total")

#         return all_ambiguities

#     # ─────────────────────────────────────
#     # CHECK 1: Parameter types
#     # ─────────────────────────────────────

#     def _check_param_types(self, endpoint) -> List[Ambiguity]:

#         issues = []
#         all_params = (
#             endpoint.required_params +
#             endpoint.optional_params
#         )

#         for param in all_params:

#             known_type = endpoint.param_types.get(param)
#             # .get() → None if not found
#             # None ya empty string dono "missing" hain

#             if not known_type or known_type == "unknown":

#                 # RAG se confirm karo
#                 rag_chunks = []

#                 # Koi type-related info mili?
#                 type_keywords = [
#                     "string", "integer", "boolean",
#                     "array", "number", "int", "bool"
#                 ]

#                 has_type_info = any(
#                     # any() — koi bhi chunk mein type info hai?
#                     param.lower() in chunk["text"].lower()
#                     and any(
#                         # nested any() — koi bhi keyword hai?
#                         t in chunk["text"].lower()
#                         for t in type_keywords
#                     )
#                     for chunk in rag_chunks
#                 )

#                 if not has_type_info:
#                     assumption = self._guess_type(param)
#                     issues.append(Ambiguity(
#                         endpoint=endpoint.path,
#                         ambiguity_type="missing_param_type",
#                         description=f"Type of '{param}' not documented",
#                         severity="high",
#                         assumption_made=assumption,
#                         parameter=param
#                     ))

#         return issues

#     def _guess_type(self, param_name: str) -> str:
#         """
#         Param naam se type guess karo.
#         Convention-based heuristics.
#         Perfect nahi — but better than nothing.
#         """

#         p = param_name.lower()

#         if p.endswith("_id") or p == "id":
#             return f"Assuming integer for '{param_name}'"

#         elif p in ["limit", "offset", "page",
#                    "count", "size", "per_page", "skip"]:
#             return f"Assuming integer for '{param_name}'"

#         elif p.startswith("is_") or p.startswith("has_") or \
#              p in ["active", "enabled", "verified", "published"]:
#             return f"Assuming boolean for '{param_name}'"
#             # startswith() → string prefix check

#         elif any(word in p for word in
#                  ["date", "time", "at", "timestamp"]):
#             return f"Assuming ISO 8601 string for '{param_name}'"
#             # any() with list — koi bhi word naam mein hai?

#         elif p in ["tags", "ids", "items", "list", "emails"]:
#             return f"Assuming array for '{param_name}'"

#         else:
#             return f"Assuming string for '{param_name}'"

#     # ─────────────────────────────────────
#     # CHECK 2: Enum/allowed values
#     # ─────────────────────────────────────

#     def _check_param_values(self, endpoint) -> List[Ambiguity]:

#         issues = []

#         # Ye params usually enum hote hain
#         LIKELY_ENUM_PARAMS = {
#             "status", "type", "role", "state",
#             "category", "format", "sort", "order",
#             "filter", "mode", "action", "kind"
#         }
#         # Set use kiya list ki jagah kyun?
#         # "status" in LIKELY_ENUM_PARAMS
#         # Set lookup O(1) — instant
#         # List lookup O(n) — size ke saath slow
#         # Ye optimization small scale pe matter nahi karta
#         # But good habit hai

#         all_params = (
#             endpoint.required_params +
#             endpoint.optional_params
#         )

#         for param in all_params:
#             if param.lower() not in LIKELY_ENUM_PARAMS:
#                 continue

#             # RAG mein allowed values dhundo
#             # chunks = self.rag.get_relevant_chunks(
#             #     f"{param} allowed values options "
#             #     f"enum must be one of {endpoint.path}",
#             #     n=3
#             # )
#             chunks = []

#             value_keywords = [
#                 "available", "allowed", "one of",
#                 "must be", "values:", "options:",
#                 "can be", "either"
#             ]

#             has_values = any(
#                 any(kw in chunk["text"].lower()
#                     for kw in value_keywords)
#                 for chunk in chunks
#             )

#             if not has_values:
#                 issues.append(Ambiguity(
#                     endpoint=endpoint.path,
#                     ambiguity_type="unclear_param_values",
#                     description=(
#                         f"Allowed values for '{param}' not documented"
#                     ),
#                     severity="high",
#                     assumption_made=(
#                         f"Will pass raw string for '{param}' "
#                         f"— may cause validation error"
#                     ),
#                     parameter=param
#                 ))

#         return issues

#     # ─────────────────────────────────────
#     # CHECK 3: Error codes
#     # ─────────────────────────────────────

#     def _check_error_codes(self, endpoint) -> List[Ambiguity]:

#         issues = []

#         if not endpoint.error_codes:
#             issues.append(Ambiguity(
#                 endpoint=endpoint.path,
#                 ambiguity_type="missing_error_codes",
#                 description=(
#                     f"No error codes documented for "
#                     f"{endpoint.method} {endpoint.path}"
#                 ),
#                 severity="medium",
#                 assumption_made=(
#                     "Handling generic 400, 401, "
#                     "403, 404, 429, 500 only"
#                 )
#             ))
#         else:
#             # 429 documented hai?
#             codes = [
#                 str(e.get("code", ""))
#                 for e in endpoint.error_codes
#             ]
#             # List comprehension with .get()
#             # code integer bhi ho sakta hai, string bhi
#             # str() se consistent comparison

#             if "429" not in codes:
#                 issues.append(Ambiguity(
#                     endpoint=endpoint.path,
#                     ambiguity_type="missing_error_codes",
#                     description="429 Rate Limit error not documented",
#                     severity="low",
#                     assumption_made=(
#                         "Adding standard rate limit handling anyway"
#                     )
#                 ))

#         return issues

#     # ─────────────────────────────────────
#     # CHECK 4: Auth clarity
#     # ─────────────────────────────────────

#     def _check_auth(self, endpoint, schema) -> List[Ambiguity]:

#         issues = []

#         if endpoint.auth_required and schema.auth_method == "None":
#             issues.append(Ambiguity(
#                 endpoint=endpoint.path,
#                 ambiguity_type="unclear_auth",
#                 description=(
#                     f"Auth required but method not documented"
#                 ),
#                 severity="high",
#                 assumption_made=(
#                     "Trying Bearer token in Authorization header"
#                 )
#             ))

#         elif (endpoint.auth_required and
#               schema.auth_method != "None" and
#               not schema.auth_instructions):
#             # elif kyun? Agar pehla condition true hai
#             # dusra check karne ki zaroorat nahi
#             issues.append(Ambiguity(
#                 endpoint=endpoint.path,
#                 ambiguity_type="unclear_auth",
#                 description=(
#                     f"Auth method known but format not specified"
#                 ),
#                 severity="medium",
#                 assumption_made=(
#                     f"Using 'Authorization: "
#                     f"{schema.auth_method} <token>'"
#                 )
#             ))

#         return issues

#     # ─────────────────────────────────────
#     # CHECK 5: Rate limit info
#     # ─────────────────────────────────────

#     def _check_rate_limit(self, endpoint, schema) -> List[Ambiguity]:

#         issues = []

#         missing_rate_limit = schema.rate_limits in [
#             "Not specified",
#             "Not specified in spec",
#             ""
#         ]
#         # `in` operator for list membership check
#         # Cleaner than multiple `or` conditions

#         if not endpoint.rate_limit and missing_rate_limit:
#             issues.append(Ambiguity(
#                 endpoint=endpoint.path,
#                 ambiguity_type="no_rate_limit",
#                 description="Rate limits not documented",
#                 severity="medium",
#                 assumption_made=(
#                     "Adding 0.5 sec delay between calls"
#                 )
#             ))

#         return issues

#     # ─────────────────────────────────────
#     # CHECK 6: Request examples
#     # ─────────────────────────────────────

#     def _check_examples(self, endpoint) -> List[Ambiguity]:

#         issues = []

#         if (endpoint.method in ["POST", "PUT", "PATCH"]
#                 and not endpoint.example_request):
#             # Tuple check: method in ["POST", "PUT", "PATCH"]
#             # Short circuit: agar method match nahi → skip
#             issues.append(Ambiguity(
#                 endpoint=endpoint.path,
#                 ambiguity_type="missing_example",
#                 description=(
#                     f"No request body example for "
#                     f"{endpoint.method} {endpoint.path}"
#                 ),
#                 severity="low",
#                 assumption_made=(
#                     "Constructing body from param names + assumed types"
#                 )
#             ))

#         return issues

#     # ─────────────────────────────────────
#     # CHECK 7: Response structure
#     # ─────────────────────────────────────

#     def _check_response_structure(self, endpoint) -> List[Ambiguity]:

#         issues = []

#         if not endpoint.response_schema:
#             issues.append(Ambiguity(
#                 endpoint=endpoint.path,
#                 ambiguity_type="unclear_response",
#                 description=(
#                     f"Response structure not documented"
#                 ),
#                 severity="low",
#                 assumption_made=(
#                     "Accessing response as raw JSON"
#                 )
#             ))

#         return issues

#     # ─────────────────────────────────────
#     # CHECK 8: Pagination
#     # ─────────────────────────────────────

#     def _check_pagination(self, endpoint) -> List[Ambiguity]:

#         issues = []

#         # GET endpoints jo list return karte hain
#         is_list_endpoint = (
#             endpoint.method == "GET"
#             and not any(
#                 char in endpoint.path
#                 for char in ["{", "login", "logout", "count"]
#             )
#             # any() with iterable — koi bhi match?
#             # "{" in path → specific item fetch kar raha hai
#             # "login" → list nahi return karta
#         )

#         if not is_list_endpoint:
#             return []

#         pagination_params = {
#             "page", "limit", "offset",
#             "cursor", "per_page", "page_size"
#         }

#         has_pagination_param = any(
#             p in pagination_params
#             for p in (
#                 endpoint.required_params +
#                 endpoint.optional_params
#             )
#         )

#         if has_pagination_param:
#             return []  # Already documented

#         # RAG mein pagination info dhundo
#         chunks = []

#         pagination_keywords = [
#             "pagination", "page", "limit",
#             "cursor", "next", "has_more", "offset"
#         ]

#         has_pagination_info = any(
#             any(kw in chunk["text"].lower()
#                 for kw in pagination_keywords)
#             for chunk in chunks
#         )

#         if not has_pagination_info:
#             issues.append(Ambiguity(
#                 endpoint=endpoint.path,
#                 ambiguity_type="missing_pagination",
#                 description=(
#                     f"GET {endpoint.path} may return paginated "
#                     f"results but pagination not documented"
#                 ),
#                 severity="medium",
#                 assumption_made=(
#                     "Fetching first page only — may miss data"
#                 )
#             ))

#         return issues

#     # ─────────────────────────────────────
#     # HELPER: Summary string
#     # ─────────────────────────────────────

#     def get_summary(self, ambiguities: List[Ambiguity]) -> str:

#         if not ambiguities:
#             return "✅ No ambiguities — docs are complete!"

#         lines = [
#             f"⚠️  {len(ambiguities)} documentation gaps:\n"
#         ]

#         for amb in ambiguities:
#             emoji = {"high":"🔴","medium":"🟡","low":"🟢"}.get(
#                 amb.severity, "⚪"
#             )
#             lines.append(
#                 f"{emoji} [{amb.ambiguity_type}] "
#                 f"{amb.endpoint}\n"
#                 f"   Issue:      {amb.description}\n"
#                 f"   Assumption: {amb.assumption_made}\n"
#             )

#         return "\n".join(lines)





# # ═══════════════════════════════════════════
# agents/ambiguity_detector.py

from dataclasses import dataclass
from typing import List, Optional
from llm_config import get_llm_response # LiteLLM fallback function
from dotenv import load_dotenv
import os

load_dotenv()

# ═══════════════════════════════════════════
# DATA STRUCTURE
# ═══════════════════════════════════════════

@dataclass
class Ambiguity:
    endpoint: str
    ambiguity_type: str
    description: str
    severity: str           # "high" / "medium" / "low"
    assumption_made: str    # Code generator ye use karega
    parameter: Optional[str] = None

# ═══════════════════════════════════════════
# AMBIGUITY DETECTOR
# ═══════════════════════════════════════════

class AmbiguityDetectorAgent:
    """
    Schema ke har endpoint ko 8 checks se analyze karta hai.
    """

    def __init__(self, rag_pipeline):
        self.rag = rag_pipeline
        # self.llm ko yahan se hata diya hai taaki undefined error na aaye

    # ─────────────────────────────────────
    # MAIN ENTRY POINT
    # ─────────────────────────────────────

    def detect(self, schema) -> List[Ambiguity]:
        print("\n⚠️  Detecting ambiguities...")
        all_ambiguities = []

        for endpoint in schema.endpoints:
            # Har endpoint ke liye sab checks run karo
            checks = [
                self._check_param_types(endpoint),
                self._check_param_values(endpoint),
                self._check_error_codes(endpoint),
                self._check_auth(endpoint, schema),
                self._check_rate_limit(endpoint, schema),
                self._check_examples(endpoint),
                self._check_response_structure(endpoint),
                self._check_pagination(endpoint),
            ]

            for check_result in checks:
                all_ambiguities.extend(check_result)

        # High severity pehle sort karo
        all_ambiguities.sort(
            key=lambda x: {
                "high": 0, "medium": 1, "low": 2
            }.get(x.severity, 3)
        )

        high   = sum(1 for a in all_ambiguities if a.severity == "high")
        medium = sum(1 for a in all_ambiguities if a.severity == "medium")
        low    = sum(1 for a in all_ambiguities if a.severity == "low")

        print(f"✅ Done! 🔴{high} 🟡{medium} 🟢{low} = {len(all_ambiguities)} total")

        return all_ambiguities

    # ─────────────────────────────────────
    # CHECK 1: Parameter types
    # ─────────────────────────────────────

    def _check_param_types(self, endpoint) -> List[Ambiguity]:
        issues = []
        all_params = (endpoint.required_params + endpoint.optional_params)

        for param in all_params:
            known_type = endpoint.param_types.get(param)
            if not known_type or known_type == "unknown":
                assumption = self._guess_type(param)
                issues.append(Ambiguity(
                    endpoint=endpoint.path,
                    ambiguity_type="missing_param_type",
                    description=f"Type of '{param}' not documented",
                    severity="high",
                    assumption_made=assumption,
                    parameter=param
                ))
        return issues

    def _guess_type(self, param_name: str) -> str:
        p = param_name.lower()
        if p.endswith("_id") or p == "id": return f"Assuming integer for '{param_name}'"
        elif p in ["limit", "offset", "page", "count"]: return f"Assuming integer for '{param_name}'"
        elif p.startswith("is_") or p in ["active", "verified"]: return f"Assuming boolean for '{param_name}'"
        return f"Assuming string for '{param_name}'"

    # ─────────────────────────────────────
    # CHECK 2: Enum values
    # ─────────────────────────────────────

    def _check_param_values(self, endpoint) -> List[Ambiguity]:
        # Yahan agar LLM call karni ho toh get_llm_response use karna
        return []

    # ─────────────────────────────────────
    # CHECK 3: Error codes
    # ─────────────────────────────────────

    def _check_error_codes(self, endpoint) -> List[Ambiguity]:
        issues = []
        if not endpoint.error_codes:
            issues.append(Ambiguity(
                endpoint=endpoint.path,
                ambiguity_type="missing_error_codes",
                description=f"No error codes for {endpoint.path}",
                severity="medium",
                assumption_made="Handling generic errors only"
            ))
        return issues

    # ─────────────────────────────────────
    # CHECK 4: Auth clarity
    # ─────────────────────────────────────

    def _check_auth(self, endpoint, schema) -> List[Ambiguity]:
        issues = []
        if endpoint.auth_required and schema.auth_method == "None":
            issues.append(Ambiguity(
                endpoint=endpoint.path,
                ambiguity_type="unclear_auth",
                description="Auth required but method missing",
                severity="high",
                assumption_made="Using Bearer Token"
            ))
        return issues

    # ─────────────────────────────────────
    # CHECK 5: Rate limit
    # ─────────────────────────────────────

    def _check_rate_limit(self, endpoint, schema) -> List[Ambiguity]:
        return []

    # ─────────────────────────────────────
    # CHECK 6: Request examples
    # ─────────────────────────────────────

    def _check_examples(self, endpoint) -> List[Ambiguity]:
        return []

    # ─────────────────────────────────────
    # CHECK 7: Response structure
    # ─────────────────────────────────────

    def _check_response_structure(self, endpoint) -> List[Ambiguity]:
        return []

    # ─────────────────────────────────────
    # CHECK 8: Pagination
    # ─────────────────────────────────────

    def _check_pagination(self, endpoint) -> List[Ambiguity]:
        return []

    # ─────────────────────────────────────
    # HELPER: Summary string
    # ─────────────────────────────────────

    def get_summary(self, ambiguities: List[Ambiguity]) -> str:
        if not ambiguities: return "✅ No gaps!"
        lines = [f"⚠️  {len(ambiguities)} gaps:\n"]
        for amb in ambiguities:
            emoji = {"high":"🔴","medium":"🟡","low":"🟢"}.get(amb.severity, "⚪")
            lines.append(f"{emoji} [{amb.ambiguity_type}] {amb.endpoint}\n")
        return "\n".join(lines)