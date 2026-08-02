# # agents/code_generator.py

# import json
# from dataclasses import dataclass
# from typing import List
# #from llm_config import get_llm_response
# #from langchain_openai import ChatOpenAI
# from langchain_google_genai import ChatGoogleGenerativeAI
# from langchain_core.prompts import ChatPromptTemplate
# from dotenv import load_dotenv
# import os

# from pydantic import SecretStr

# load_dotenv()

# # ═══════════════════════════════════════════
# # DATA STRUCTURE
# # ═══════════════════════════════════════════

# @dataclass
# class GeneratedCode:
#     code: str
#     endpoints_used: List[str]
#     execution_order: List[str]
#     assumptions: List[str]
#     language: str = "python"


# # ═══════════════════════════════════════════
# # CODE GENERATOR AGENT
# # ═══════════════════════════════════════════

# class CodeGeneratorAgent:
#     """
#     Schema + DepMap + Ambiguities → First draft code.

#     Ye "first draft" hai — intentionally incomplete.
#     Adversarial agent isko todega.
#     Hardener agent fix karega.
#     Final code tab niklega.
#     """

#     # System prompt = permanent instructions
#     # Ye har generation mein apply hoga
#     SYSTEM_PROMPT = """You are a senior Python developer
# specializing in API integrations.

# Your code must follow ALL of these rules:
# 1. Use 'httpx' library — not requests
# 2. Use environment variables for ALL credentials
#    (os.getenv("API_KEY") — never hardcode)
# 3. Add type hints to every function parameter and return
# 4. Add docstring to every function
# 5. Follow the EXACT execution order provided
# 6. Use the base URL from schema — never guess
# 7. Pass output of one call as input to next
#    (pet_id = create_pet()["id"] then get_pet(pet_id))
# 8. Print progress so user knows what is happening
# 9. Wrap everything in main() function
# 10. End with: if __name__ == '__main__': main()

# Return ONLY Python code.
# No explanation. No markdown backticks. Just code."""

#     def __init__(self):
#         # self.llm = ChatGroq(
#         #     model="llama-3.3-70b-versatile",
#         #     # gpt-4o kyun? gpt-4o-mini nahi?
#         #     # Code generation quality matter karta hai
#         #     # gpt-4o better code likhta hai
#         #     # Adversarial testing mein zyada attacks survive karta hai
#         #     # Cost: slightly more but worth it
#         #     temperature=0.1,
#         #     api_key=SecretStr(os.getenv("GROQ_API_KEY") or "")
#         # )
#         self.llm = ChatGoogleGenerativeAI(
#     model="gemini-2.5-flash-lite",
#     google_api_key=os.getenv("GEMINI_API_KEY"),
#     temperature=0.1
# )
#     # ─────────────────────────────────────
#     # MAIN ENTRY POINT
#     # ─────────────────────────────────────

#     def generate(
#         self,
#         schema,
#         dep_map,
#         ambiguities,
#         user_task: str
#     ) -> GeneratedCode:

#         print("\n💻 Generating code...")
#         print(f"   Task: {user_task}")

#         # Step 1: Relevant endpoints dhundo
#         relevant_endpoints = self._find_relevant_endpoints(
#             schema, dep_map, user_task
#         )
#         print(f"   Endpoints: "
#               f"{[ep.method+' '+ep.path for ep in relevant_endpoints]}")

#         # Step 2: Assumptions compile karo
#         assumptions = [a.assumption_made for a in ambiguities]

#         # Step 3: Prompt banao
#         prompt = self._build_prompt(
#             schema, relevant_endpoints,
#             dep_map, assumptions, user_task
#         )

#         # Step 4: Code generate karo
#         response = self.llm.invoke(prompt)
#         code = self._clean_code(str(response.content))

#         print(f"✅ Code generated! Lines: {len(code.splitlines())}")

#         return GeneratedCode(
#             code=code,
#             endpoints_used=[ep.path for ep in relevant_endpoints],
#             execution_order=dep_map.execution_order,
#             assumptions=assumptions
#         )

#     # ─────────────────────────────────────
#     # HELPER 1: Relevant endpoints
#     # User task se decide karo kaun se use karein
#     # ─────────────────────────────────────

#     def _find_relevant_endpoints(
#         self, schema, dep_map, user_task: str
#     ) -> list:
#         """
#         LLM se poochho: is task ke liye kaun se endpoints?

#         Kyun LLM? Rule-based nahi?
#         Task natural language mein hai:
#         "Create a pet and fetch it"
#         Rule-based se "create" → POST aur "fetch" → GET
#         but exact paths? LLM better hai.
#         """

#         endpoint_list = "\n".join([
#             f"- {ep.method} {ep.path}: {ep.description}"
#             for ep in schema.endpoints
#         ])

#         prompt = f"""
# User task: {user_task}

# Available endpoints:
# {endpoint_list}

# Which endpoints are needed to complete this task?
# Return ONLY a JSON array of paths:
# ["/path1", "/path2"]
# No explanation. Just the JSON array.
# """
#         response = self.llm.invoke(prompt)

#         try:
#             raw = str(response.content).strip()

#             # JSON extract
#             if "```" in raw:
#                 raw = raw.split("```")[1]
#                 if raw.startswith("json"):
#                     raw = raw[4:]
#                 raw = raw.split("```")[0]

#             needed_paths = json.loads(raw.strip())

#             # Dependency order follow karo
#             relevant = []
#             seen = set()

#             # Pehle dep_map order mein dhundo
#             for path in dep_map.execution_order:
#                 if path in needed_paths and path not in seen:
#                     ep = next(
#                         (e for e in schema.endpoints if e.path == path),
#                         None
#                         # next() → generator ka pehla element lo
#                         # (e for e in list if condition) → generator
#                         # None → agar koi na mila toh None
#                     )
#                     if ep:
#                         relevant.append(ep)
#                         seen.add(path)

#             # Jo order mein nahi the unhe bhi add karo
#             for path in needed_paths:
#                 if path not in seen:
#                     ep = next(
#                         (e for e in schema.endpoints if e.path == path),
#                         None
#                     )
#                     if ep:
#                         relevant.append(ep)
#                         seen.add(path)

#             return relevant if relevant else schema.endpoints[:3]
#             # Fallback: pehle 3 endpoints
#             # Agar LLM kuch useful nahi deta

#         except Exception:
#             return schema.endpoints[:3]

#     # ─────────────────────────────────────
#     # HELPER 2: Detailed prompt
#     # ─────────────────────────────────────

#     def _build_prompt(
#         self, schema, endpoints,
#         dep_map, assumptions, user_task
#     ) -> str:
#         """
#         Structured prompt kyun?

#         f-string directly bana sakte the
#         But sections clearly separate karna
#         LLM ke liye easier hai process karna.

#         "===" headers → LLM ko sections clearly dikhte hain
#         """

#         # Endpoint details
#         endpoint_details = []
#         for ep in endpoints:
#             detail = (
#                 f"\nEndpoint: {ep.method} {ep.path}\n"
#                 f"Description: {ep.description}\n"
#                 f"Required params: {ep.required_params}\n"
#                 f"Optional params: {ep.optional_params}\n"
#                 f"Param types: {ep.param_types}\n"
#                 f"Auth required: {ep.auth_required}\n"
#                 f"Error codes: {ep.error_codes}\n"
#             )
#             endpoint_details.append(detail)

#         # Assumptions text
#         assumptions_text = "\n".join([
#             f"- {a}" for a in assumptions[:10]
#             # [:10] kyun? Bahut zyada assumptions confuse karte hain
#             # Top 10 enough hai
#         ]) if assumptions else "None documented"

#         # Execution order
#         order_text = "\n".join([
#             f"{i+1}. {path}"
#             for i, path in enumerate(
#                 [ep.path for ep in endpoints]
#             )
#         ])

#         return f"""
# {self.SYSTEM_PROMPT}

# === API INFORMATION ===
# API Name: {schema.api_name}
# Base URL: {schema.base_url}
# Auth Method: {schema.auth_method}
# Auth Instructions: {schema.auth_instructions}
# Global Headers: {schema.global_headers}
# Rate Limits: {schema.rate_limits}

# === ENDPOINTS TO USE ===
# {"".join(endpoint_details)}

# === EXECUTION ORDER ===
# Call in this EXACT order:
# {order_text}

# === DOCUMENTATION GAPS & ASSUMPTIONS ===
# (These were unclear in docs — using these assumptions)
# {assumptions_text}

# === CRITICAL: DATA PASSING ===
# Store each API response and pass to next call:
# Example:
#   pet = create_pet(...)        # Returns dict with 'id'
#   pet_id = pet['id']           # Extract id
#   result = get_pet(pet_id)     # Pass to next call

# === USER TASK ===
# {user_task}

# Generate complete Python code:
# """

#     # ─────────────────────────────────────
#     # HELPER 3: Code clean karo
#     # ─────────────────────────────────────

#     def _clean_code(self, raw: str) -> str:
#         """
#         LLM kabhi kabhi markdown mein wrap karta hai:
# ```python
#         import httpx
#         ...
# ```
#         Strip karo → sirf code chahiye
#         """

#         if "```python" in raw:
#             start = raw.find("```python") + 9
#             # +9 kyun? "```python" = 9 characters
#             end = raw.find("```", start)
#             # start se aage dhundo → closing ``` milega
#             if end > start:
#                 return raw[start:end].strip()

#         elif "```" in raw:
#             start = raw.find("```") + 3
#             end = raw.find("```", start)
#             if end > start:
#                 return raw[start:end].strip()

#         return raw.strip()










# agents/code_generator.py

import json
import time
from dataclasses import dataclass
from typing import List
#from llm_config import get_llm_response
#from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv
import os

from pydantic import SecretStr

from llm_config import get_llm_response

load_dotenv()

# ═══════════════════════════════════════════
# DATA STRUCTURE
# ═══════════════════════════════════════════

@dataclass
class GeneratedCode:
    code: str
    endpoints_used: List[str]
    execution_order: List[str]
    assumptions: List[str]
    language: str = "python"


# ═══════════════════════════════════════════
# CODE GENERATOR AGENT
# ═══════════════════════════════════════════

class CodeGeneratorAgent:
    """
    Schema + DepMap + Ambiguities → First draft code.

    Ye "first draft" hai — intentionally incomplete.
    Adversarial agent isko todega.
    Hardener agent fix karega.
    Final code tab niklega.
    """

    # System prompt = permanent instructions
    # Ye har generation mein apply hoga
    SYSTEM_PROMPT = """You are a senior Python developer
specializing in API integrations.

Your code must follow ALL of these rules:
1. Use 'httpx' library — not requests
2. Use environment variables for ALL credentials
   (os.getenv("API_KEY") — never hardcode)
3. Add type hints to every function parameter and return
4. Add docstring to every function
5. Follow the EXACT execution order provided
6. Use the base URL from schema — never guess
7. Pass output of one call as input to next
   (pet_id = create_pet()["id"] then get_pet(pet_id))
8. Print progress so user knows what is happening
9. Wrap everything in main() function
10. End with: if __name__ == '__main__': main()

Return ONLY Python code.
No explanation. No markdown backticks. Just code."""

    def __init__(self):
        # self.llm = ChatGroq(
        #     model="llama-3.3-70b-versatile",
        #     # gpt-4o kyun? gpt-4o-mini nahi?
        #     # Code generation quality matter karta hai
        #     # gpt-4o better code likhta hai
        #     # Adversarial testing mein zyada attacks survive karta hai
        #     # Cost: slightly more but worth it
        #     temperature=0.1,
        #     api_key=SecretStr(os.getenv("GROQ_API_KEY") or "")
        # )
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash-lite",
            google_api_key=os.getenv("GEMINI_API_KEY"),
            temperature=0.1
        )
        
    # ─────────────────────────────────────
    # MAIN ENTRY POINT
    # ─────────────────────────────────────

    def generate(
        self,
        schema,
        dep_map,
        ambiguities,
        user_task: str
    ) -> GeneratedCode:

        print("\n💻 Generating code...")
        print(f"   Task: {user_task}")

        # Step 1: Relevant endpoints dhundo
        relevant_endpoints = self._find_relevant_endpoints(
            schema, dep_map, user_task
        )
        print(f"   Endpoints: "
              f"{[ep.method+' '+ep.path for ep in relevant_endpoints]}")

        # Step 2: Assumptions compile karo
        assumptions = [a.assumption_made for a in ambiguities]

        # Step 3: Prompt banao
        prompt = self._build_prompt(
            schema, relevant_endpoints,
            dep_map, assumptions, user_task
        )

        # Step 4: Code generate karo (WITH QUOTA PROTECTION)
        # while True:
        #     try:
        #         response = self.llm.invoke(prompt)
        #         break
        #     except Exception as e:
        #         if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
        #             print("\n⏳ Gemini 20 RPM limit hit. Cooling down for 61 seconds...")
        #             time.sleep(61)
        #         else:
        #             raise e
        # Step 4: Code generate karo (Using YOUR universal router)
        response_text = get_llm_response(prompt)
        code = self._clean_code(response_text)

        print(f"✅ Code generated! Lines: {len(code.splitlines())}")

        return GeneratedCode(
            code=code,
            endpoints_used=[ep.path for ep in relevant_endpoints],
            execution_order=dep_map.execution_order,
            assumptions=assumptions
        )

    # ─────────────────────────────────────
    # HELPER 1: Relevant endpoints
    # User task se decide karo kaun se use karein
    # ─────────────────────────────────────

    def _find_relevant_endpoints(
        self, schema, dep_map, user_task: str
    ) -> list:
        """
        LLM se poochho: is task ke liye kaun se endpoints?

        Kyun LLM? Rule-based nahi?
        Task natural language mein hai:
        "Create a pet and fetch it"
        Rule-based se "create" → POST aur "fetch" → GET
        but exact paths? LLM better hai.
        """

        endpoint_list = "\n".join([
            f"- {ep.method} {ep.path}: {ep.description}"
            for ep in schema.endpoints
        ])

        prompt = f"""
User task: {user_task}

Available endpoints:
{endpoint_list}

Which endpoints are needed to complete this task?
Return ONLY a JSON array of paths:
["/path1", "/path2"]
No explanation. Just the JSON array.
"""
        # # QUOTA PROTECTION FOR ENDPOINT SEARCH
        # while True:
        #     try:
        #         response = self.llm.invoke(prompt)
        #         break
        #     except Exception as e:
        #         if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
        #             print("\n⏳ Gemini 20 RPM limit hit. Cooling down for 61 seconds...")
        #             time.sleep(61)
        #         else:
        #             raise e
        response_text = get_llm_response(prompt)
        try:
            raw = str(response_text).strip()

            # JSON extract
            if "```" in raw:
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
                raw = raw.split("```")[0]

            needed_paths = json.loads(raw.strip())

            # Dependency order follow karo
            relevant = []
            seen = set()

            # Pehle dep_map order mein dhundo
            for path in dep_map.execution_order:
                if path in needed_paths and path not in seen:
                    ep = next(
                        (e for e in schema.endpoints if e.path == path),
                        None
                    )
                    if ep:
                        relevant.append(ep)
                        seen.add(path)

            # Jo order mein nahi the unhe bhi add karo
            for path in needed_paths:
                if path not in seen:
                    ep = next(
                        (e for e in schema.endpoints if e.path == path),
                        None
                    )
                    if ep:
                        relevant.append(ep)
                        seen.add(path)

            return relevant if relevant else schema.endpoints[:3]

        except Exception:
            return schema.endpoints[:3]

    # ─────────────────────────────────────
    # HELPER 2: Detailed prompt
    # ─────────────────────────────────────

    def _build_prompt(
        self, schema, endpoints,
        dep_map, assumptions, user_task
    ) -> str:
        
        # Endpoint details
        endpoint_details = []
        for ep in endpoints:
            detail = (
                f"\nEndpoint: {ep.method} {ep.path}\n"
                f"Description: {ep.description}\n"
                f"Required params: {ep.required_params}\n"
                f"Optional params: {ep.optional_params}\n"
                f"Param types: {ep.param_types}\n"
                f"Auth required: {ep.auth_required}\n"
                f"Error codes: {ep.error_codes}\n"
            )
            endpoint_details.append(detail)

        # Assumptions text
        assumptions_text = "\n".join([
            f"- {a}" for a in assumptions[:10]
        ]) if assumptions else "None documented"

        # Execution order
        order_text = "\n".join([
            f"{i+1}. {path}"
            for i, path in enumerate(
                [ep.path for ep in endpoints]
            )
        ])

        return f"""
{self.SYSTEM_PROMPT}

=== API INFORMATION ===
API Name: {schema.api_name}
Base URL: {schema.base_url}
Auth Method: {schema.auth_method}
Auth Instructions: {schema.auth_instructions}
Global Headers: {schema.global_headers}
Rate Limits: {schema.rate_limits}

=== ENDPOINTS TO USE ===
{"".join(endpoint_details)}

=== EXECUTION ORDER ===
Call in this EXACT order:
{order_text}

=== DOCUMENTATION GAPS & ASSUMPTIONS ===
(These were unclear in docs — using these assumptions)
{assumptions_text}

=== CRITICAL: DATA PASSING ===
Store each API response and pass to next call:
Example:
  pet = create_pet(...)        # Returns dict with 'id'
  pet_id = pet['id']           # Extract id
  result = get_pet(pet_id)     # Pass to next call

=== USER TASK ===
{user_task}

Generate complete Python code:
"""

    # ─────────────────────────────────────
    # HELPER 3: Code clean karo
    # ─────────────────────────────────────

    def _clean_code(self, raw: str) -> str:
        
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