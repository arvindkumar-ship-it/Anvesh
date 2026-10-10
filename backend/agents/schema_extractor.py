# agents/schema_extractor.py

import json
from langchain_core.prompts import ChatPromptTemplate
from llm_config import get_llm_response
from pydantic import SecretStr
from dotenv import load_dotenv
import os
import re

from models.schemas import APISchema, EndpointSchema

load_dotenv()


class SchemaExtractorAgent:
    """
    2 strategies:
    1. OpenAPI JSON → directly parse (fast, free)
    2. HTML/PDF → RAG + LLM (slower, costs API)
    """

    def __init__(self, rag_pipeline):
        self.rag = rag_pipeline
        from langchain_core.prompts import ChatPromptTemplate
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", "Extract API Schema"),
            ("human", "{url_context} {auth_context} {endpoint_context} {rate_context}")
        ])
        # Dependency Injection kyun?
        # RAG pipeline bahar se inject karo
        # Agent khud nahi banata RAG ko
        # Fayda: Testing mein mock RAG de sakte ho
        # Fayda: Ek RAG multiple agents share karte hain
        # self.llm = ChatGroq(
        #     model="llama3-8b-8192",
        #     temperature=0,
        #     api_key=SecretStr(os.getenv("GROQ_API_KEY") or "")
        #     )

    # ─────────────────────────────────────
    # MAIN ENTRY POINT
    # ─────────────────────────────────────

    def extract(self, ingested_doc) -> APISchema:

        print("\n🔍 Extracting API Schema...")

        if ingested_doc.format_type == "openapi":
            print("   Strategy: Direct OpenAPI parsing")
            schema = self._parse_openapi(ingested_doc)
        else:
            print("   Strategy: RAG + LLM extraction")
            schema = self._extract_via_llm(ingested_doc)

        # total_endpoints calculate karo
        schema.total_endpoints = len(schema.endpoints)

        print(f"✅ Schema extracted!")
        print(f"   API: {schema.api_name}")
        print(f"   Endpoints: {schema.total_endpoints}")
        print(f"   Auth: {schema.auth_method}")

        return schema
    # 
    # def _extract_via_llm(self, ingested_doc) -> APISchema:
    #     # 1. Pehle chunks nikal lo (Inke bina error aayega)
    #     url_chunks = self.rag.get_relevant_chunks("base url and api name")
    #     auth_chunks = self.rag.get_relevant_chunks("authentication and security")
    #     endpoint_chunks = self.rag.get_relevant_chunks("endpoints and paths")
    #     rate_chunks = self.rag.get_relevant_chunks("rate limits and quotas")

    #     # Chunks ko text mein convert karne ka helper
    #     def chunks_to_context(chunks):
    #         return "\n".join([c.page_content for c in chunks])

    #     # 2. Messages format karo
    #     messages = self.prompt.format_messages(
    #         url_context=chunks_to_context(url_chunks),
    #         auth_context=chunks_to_context(auth_chunks),
    #         endpoint_context=chunks_to_context(endpoint_chunks),
    #         rate_context=chunks_to_context(rate_chunks)
    #     )

    #     # 3. get_llm_response call
    #     result = get_llm_response(messages, response_format=APISchema)

    #     result.total_endpoints = len(result.endpoints)
    #     return result
    # ─────────────────────────────────────
    # STRATEGY 1: Direct OpenAPI Parse
    # ─────────────────────────────────────

    def _parse_openapi(self, ingested_doc) -> APISchema:

        spec = json.loads(ingested_doc.raw_text)
        # ingested_doc.raw_text = JSON string
        # json.loads() → Python dictionary
        # json.dumps() = dict → string (opposite)

        # ── Base Info ──
        info = spec.get("info", {})
        servers = spec.get("servers", [])
        base_url = ""

        if servers:
            base_url = servers[0].get("url", "")
            # [0] kyun? Pehla server use karo
            # Multiple servers ho sakte hain
            # (dev, staging, prod) — pehla usually main hai
        elif "host" in spec:
            # Swagger 2.0 format
            scheme = spec.get("schemes", ["https"])[0]
            base_url = (
                f"{scheme}://{spec['host']}"
                f"{spec.get('basePath', '')}"
            )

        # ── Auth Method Detect ──
        auth_method = "None"
        auth_instructions = ""

        security_defs = (
            spec.get("securityDefinitions", {}) or
            spec.get("components", {})
                .get("securitySchemes", {})
            # "or" kyun?
            # securityDefinitions → Swagger 2.0
            # components.securitySchemes → OpenAPI 3.0
            # Dono try karo, jo milega woh use karo
        )

        if security_defs:
            for name, definition in security_defs.items():
                sec_type = definition.get("type", "")

                if sec_type == "apiKey":
                    auth_method = "API-Key"
                    location = definition.get("in", "header")
                    param_name = definition.get("name", "X-API-Key")
                    auth_instructions = (
                        f"Add '{param_name}' to {location}"
                    )

                elif sec_type in ["oauth2", "oauth"]:
                    auth_method = "OAuth2"
                    auth_instructions = "Use OAuth2 flow"

                elif sec_type == "http":
                    scheme = definition.get("scheme", "bearer")
                    auth_method = scheme.capitalize()
                    auth_instructions = (
                        f"Add 'Authorization: "
                        f"{scheme.capitalize()} <token>' header"
                    )

                break
                # break kyun?
                # Pehla security definition enough hai
                # Multiple security schemes hote hain kabhi kabhi
                # But primary one pehla hota hai

        # ── Endpoints Parse ──
        endpoints = []
        paths = spec.get("paths", {})

        for path, path_data in paths.items():
            # path = "/pet", "/user/{userId}"
            # path_data = {"get": {...}, "post": {...}}

            path_level_params = path_data.get("parameters", [])
            # Path level params = sab methods pe apply hote hain
            # e.g., /user/{userId} mein userId sab methods ka param

            for method, method_data in path_data.items():

                if method not in [
                    "get", "post", "put",
                    "delete", "patch", "head"
                ]:
                    continue
                # continue kyun?
                # path_data mein "parameters", "summary" bhi ho sakte hain
                # Sirf HTTP methods process karo

                if not isinstance(method_data, dict):
                    continue
                # isinstance() check kyun?
                # Kabhi kabhi path_data mein non-dict values hoti hain
                # Crash prevent karo

                # ── Parameters ──
                all_params = (
                    path_level_params +
                    method_data.get("parameters", [])
                    # Path params + Method specific params
                )

                required_params = []
                optional_params = []
                param_types = {}

                for param in all_params:
                    if not isinstance(param, dict):
                        continue

                    param_name = param.get("name", "")
                    is_required = param.get("required", False)

                    # Type nikalo
                    schema_info = param.get("schema", param)
                    # OpenAPI 3.0: type "schema" object mein hota hai
                    # Swagger 2.0: type directly param mein hota hai
                    # .get("schema", param) → dono handle karta hai

                    param_type = schema_info.get("type", "string")

                    param_types[param_name] = param_type

                    if is_required:
                        required_params.append(param_name)
                    else:
                        optional_params.append(param_name)

                # ── Request Body (POST/PUT ke liye) ──
                request_body = method_data.get("requestBody", {})
                if request_body:
                    content = request_body.get("content", {})

                    for content_type, content_data in content.items():
                        # content_type = "application/json"
                        body_schema = content_data.get("schema", {})
                        body_required = body_schema.get("required", [])
                        body_props = body_schema.get("properties", {})

                        for prop_name, prop_data in body_props.items():
                            param_types[prop_name] = prop_data.get(
                                "type", "string"
                            )
                            if prop_name in body_required:
                                required_params.append(prop_name)
                            else:
                                optional_params.append(prop_name)

                # ── Error Codes ──
                error_codes = []
                responses = method_data.get("responses", {})

                for code, response_data in responses.items():
                    if isinstance(response_data, dict):
                        desc = response_data.get("description", "")
                        error_codes.append({
                            "code": (
                                int(code)
                                if str(code).isdigit()
                                else code
                            ),
                            # isdigit() kyun?
                            # "200" → 200 (int)
                            # "default" → "default" (string raha)
                            "meaning": desc
                        })

                # ── Auth Required? ──
                endpoint_security = (
                    method_data.get("security") or
                    spec.get("security")
                    # Endpoint level security ya global security
                )
                auth_required = bool(endpoint_security)
                # bool() kyun?
                # endpoint_security list ho sakta hai
                # bool([]) = False, bool([{}]) = True

                endpoints.append(EndpointSchema(
                    method=method.upper(),
                    # .upper() kyun? "get" → "GET"
                    # Spec lowercase mein hota hai
                    # Hum uppercase convention follow karte hain
                    path=path,
                    description=method_data.get(
                        "summary",
                        method_data.get("description", "")
                        # "summary" prefer karo — shorter
                        # nahi hai toh "description" lo
                    ),
                    required_params=required_params,
                    optional_params=optional_params,
                    param_types=param_types,
                    auth_required=auth_required,
                    auth_type=auth_method if auth_required else None,
                    error_codes=error_codes,
                    response_schema={}
                ))

        return APISchema(
            api_name=info.get("title", "Unknown API"),
            base_url=base_url,
            auth_method=auth_method,
            auth_instructions=auth_instructions,
            global_headers={"Content-Type": "application/json"},
            rate_limits="Not specified in spec",
            endpoints=endpoints,
            api_version=info.get("version", "")
        )

    # ─────────────────────────────────────
    # STRATEGY 2: RAG + LLM
    # HTML ya PDF ke liye
    # ─────────────────────────────────────
    def _extract_via_llm(self, ingested_doc) -> APISchema:
        print("   Fetching relevant chunks from RAG...")

        # --- 1. Context Taiyaar Karo ---
        auth_chunks = self.rag.get_relevant_chunks("authentication API key token bearer authorization", n=4)
        endpoint_chunks = self.rag.get_relevant_chunks("endpoints routes GET POST PUT DELETE parameters required", n=6)
        rate_chunks = self.rag.get_relevant_chunks("rate limit requests per minute hour throttle quota", n=3)
        url_chunks = self.rag.get_relevant_chunks("base URL server host API root endpoint", n=3)

        def chunks_to_context(chunks: list) -> str:
            # Safe check for dict or LangChain objects
            return "\n".join([c["text"] if isinstance(c, dict) else getattr(c, 'page_content', str(c)) for c in chunks])

        try:
            # --- 2. Messages bhejo ---
            messages = self.prompt.format_messages(
                url_context=chunks_to_context(url_chunks),
                auth_context=chunks_to_context(auth_chunks),
                endpoint_context=chunks_to_context(endpoint_chunks),
                rate_context=chunks_to_context(rate_chunks)
            )

            # System prompt ko force karo JSON ke liye
            messages[0].content += "\nReturn ONLY a valid JSON object matching the APISchema structure. No conversational text."

            # --- 3. LLM Call aur String check ---
            result = get_llm_response(messages)

            # AGAR LLM NE STRING RETURN KI (Fallback case)
            if isinstance(result, str):
                # JSON extract karo block se
                json_match = re.search(r'\{.*\}', result, re.DOTALL)
                if json_match:
                    data = json.loads(json_match.group())
                    return APISchema(**data)
                else:
                    raise ValueError("No JSON found in LLM string")
            
            return result

        except Exception as e:
            print(f"   ⚠️  LLM extraction failed: {e}")
            print("   Returning minimal schema...")
            # Ye fallback object line 57 ko crash hone se bachayega
            return APISchema(
                api_name="Unknown API",
                base_url=getattr(ingested_doc, 'source_url', ""),
                auth_method="Unknown",
                endpoints=[]
            )

#         print("   Fetching relevant chunks from RAG...")

#         # Targeted queries — specific info dhundo
#         auth_chunks = self.rag.get_relevant_chunks(
#             "authentication API key token bearer authorization",
#             n=4
#         )
#         endpoint_chunks = self.rag.get_relevant_chunks(
#             "endpoints routes GET POST PUT DELETE parameters required",
#             n=6
#             # n=6 kyun? Endpoints zyada hote hain
#             # Zyada context chahiye
#         )
#         rate_chunks = self.rag.get_relevant_chunks(
#             "rate limit requests per minute hour throttle quota",
#             n=3
#         )
#         url_chunks = self.rag.get_relevant_chunks(
#             "base URL server host API root endpoint",
#             n=3
#         )

#         # Chunks ko readable context mein convert karo
#         def chunks_to_context(chunks: list) -> str:
#             return "\n".join([c["text"] for c in chunks])
#             # list comprehension → har chunk ka text nikalo
#             # "\n".join() → newline se join karo

#         # LLM se structured output lo
#         prompt = ChatPromptTemplate.from_messages([
#             ("system", """You are an API documentation parser.
# Extract complete API schema from documentation chunks.
# Return structured data exactly matching the required format.
# If information is missing, use empty string or empty list."""),

#             ("human", """
# Extract API schema from these documentation sections.

# BASE URL INFO:
# {url_context}

# AUTH INFO:
# {auth_context}

# ENDPOINTS INFO:
# {endpoint_context}

# RATE LIMITS INFO:
# {rate_context}

# Extract complete APISchema with all endpoints found.
# """)
#         ])

#         # chain = prompt | self.llm.with_structured_output(APISchema)
#         # # prompt → LLM → automatically APISchema object
#         # # with_structured_output(APISchema) magic:
#         # # 1. APISchema → JSON Schema banaya
#         # # 2. OpenAI function calling use kiya
#         # # 3. Response → APISchema object

#         # try:
#         #     result = chain.invoke({
#         #         "url_context": chunks_to_context(url_chunks),
#         #         "auth_context": chunks_to_context(auth_chunks),
#         #         "endpoint_context": chunks_to_context(endpoint_chunks),
#         #         "rate_context": chunks_to_context(rate_chunks)
#         #     })

#         #     result.total_endpoints = len(result.endpoints) #type: ignore[union-attr]
#         try:
#             # 2. Messages taiyaar karo
#             messages = self.prompt.format_messages(
#                 url_context=chunks_to_context(url_chunks),
#                 auth_context=chunks_to_context(auth_chunks),
#                 endpoint_context=chunks_to_context(endpoint_chunks),
#                 rate_context=chunks_to_context(rate_chunks)
#             )

#             # 3. get_llm_response call karo (Structured Output ke liye)
#             result = get_llm_response(messages, response_format=APISchema)
#             return result #type: ignore[return-value]

#         except Exception as e:
#             print(f"   ⚠️  LLM extraction failed: {e}")
#             print("   Returning minimal schema...")

#             # Fallback — empty schema
#             # Program crash nahi hona chahiye
#             # Graceful degradation — kuch toh do
#             return APISchema(
#                 api_name="Unknown API",
#                 base_url=ingested_doc.source_url,
#                 auth_method="Unknown",
#                 endpoints=[]
#             )
