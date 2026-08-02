# from pipelines.rag_pipeline import HermesRAGPipeline
# from types import SimpleNamespace
# from typing import Any
# class DependencyMapperAgent:
#     def __init__(self, rag: HermesRAGPipeline):
#         self.rag = rag

#     def map(self, schema: Any) -> Any:
#         query = f"What are the dependencies between these API endpoints: {schema}"
#         #result = self.rag.query(question=query) #type: ignore[attr-defined]
#         # return {"dependencies": result}
#         result = "Dependencies mapped based on schema analysis"
#         return SimpleNamespace(
#             execution_order=[],
#             dependencies=result,
#             has_circular=False,
#             independent_endpoints=[],
#             dependency_details=[]
#         )

# agents/dependency_mapper.py

import re
import json
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from llm_config import get_llm_response
from langchain_core.prompts import ChatPromptTemplate
import networkx as nx
from dotenv import load_dotenv
import os

load_dotenv()

@dataclass
class Dependency:
    endpoint: str
    depends_on: str
    reason: str
    required_output: str

@dataclass
class DependencyMap:
    execution_order: List[str]
    dependencies: Dict[str, List[str]]
    dependency_details: List[Dependency]
    has_circular: bool
    independent_endpoints: List[str]


class DependencyMapperAgent:

    def __init__(self, rag_pipeline):
        self.rag = rag_pipeline
        # self.llm = ChatGroq(
        #     model="llama-3.3-70b-versatile",
        #     temperature=0,
        #     groq_api_key=os.getenv("GROQ_API_KEY")
        # )

    def map(self, schema) -> DependencyMap:

        print("\n🗺️  Mapping dependencies...")

        G = nx.DiGraph()

        for ep in schema.endpoints:
            G.add_node(ep.path, method=ep.method)

        all_dependencies = []

        print("   Detection 1: Path variables...")
        path_deps = self._detect_path_variable_deps(schema, G)
        all_dependencies.extend(path_deps)

        print("   Detection 2: Parameter names...")
        param_deps = self._detect_param_deps(schema, G)
        all_dependencies.extend(param_deps)

        if len(schema.endpoints) <= 20:
            print("   Detection 3: LLM semantic analysis...")
            llm_deps = self._detect_llm_deps(schema, G)
            all_dependencies.extend(llm_deps)
        else:
            print("   Detection 3: Skipped (too many endpoints)")

        has_circular = not nx.is_directed_acyclic_graph(G)

        if has_circular:
            print("   ⚠️  Circular dependency! Resolving...")
            cycles = list(nx.simple_cycles(G))
            for cycle in cycles:
                if len(cycle) >= 2:
                    if G.has_edge(cycle[0], cycle[1]):
                        G.remove_edge(cycle[0], cycle[1])
                    elif G.has_edge(cycle[1], cycle[0]):
                        G.remove_edge(cycle[1], cycle[0])

        try:
            execution_order = list(nx.topological_sort(G))
        except nx.NetworkXUnfeasible:
            execution_order = [ep.path for ep in schema.endpoints]

        independent = [
            node for node in G.nodes()
            if G.in_degree(node) == 0 and G.out_degree(node) == 0
        ]

        deps_dict = {
            node: list(G.predecessors(node))
            for node in G.nodes()
        }

        print(f"✅ Done! Order: {len(execution_order)} steps, "
              f"Deps: {len(all_dependencies)}, "
              f"Independent: {len(independent)}")

        return DependencyMap(
            execution_order=execution_order,
            dependencies=deps_dict,
            dependency_details=all_dependencies,
            has_circular=has_circular,
            independent_endpoints=independent
        )

    def _detect_path_variable_deps(
        self, schema, G: nx.DiGraph
    ) -> List[Dependency]:

        dependencies = []

        for endpoint in schema.endpoints:

            # {petId}, {orderId}, {username} sab catch karta hai
            path_vars = re.findall(r'\{(\w+)\}', endpoint.path)

            for var in path_vars:
                source = self._find_creator(var, endpoint.path, schema)

                if source and source != endpoint.path:
                    G.add_edge(source, endpoint.path, variable=var)
                    dependencies.append(Dependency(
                        endpoint=endpoint.path,
                        depends_on=source,
                        reason=f"Path variable '{{{var}}}' from {source}",
                        required_output=var
                    ))

        return dependencies

    def _find_creator(
        self,
        variable: str,
        current_path: str,
        schema
    ) -> Optional[str]:

        # camelCase aur snake_case dono handle karta hai
        # petId → pet, orderId → order, pet_id → pet
        resource = re.sub(r'[Ii]d$', '', variable).lower().rstrip('_')

        if not resource:
            return None

        best_match = None
        best_score = 0

        for ep in schema.endpoints:
            if ep.path == current_path:
                continue

            score = 0
            ep_path_lower = ep.path.lower()

            if ep.method == "POST" and f"/{resource}" in ep_path_lower:
                score += 10

            if resource in ep_path_lower:
                score += 5

            if (ep.method == "GET"
                    and "{" not in ep.path
                    and resource in ep_path_lower):
                score += 3

            if score > best_score:
                best_score = score
                best_match = ep.path

        return best_match if best_score > 0 else None

    def _detect_param_deps(
        self, schema, G: nx.DiGraph
    ) -> List[Dependency]:

        dependencies = []

        for endpoint in schema.endpoints:
            for param in endpoint.required_params:

                # camelCase (petId) aur snake_case (pet_id) dono
                is_id_param = (
                    param.endswith("_id") or
                    param.endswith("Id")
                )

                if not is_id_param:
                    continue

                # resource nikalo — dono formats se
                resource = param.replace("_id", "").replace("Id", "").lower()

                for other_ep in schema.endpoints:
                    if other_ep.path == endpoint.path:
                        continue

                    if (other_ep.method == "POST"
                            and resource in other_ep.path.lower()
                            and "{" not in other_ep.path):

                        if not G.has_edge(other_ep.path, endpoint.path):
                            G.add_edge(
                                other_ep.path,
                                endpoint.path,
                                param=param
                            )
                            dependencies.append(Dependency(
                                endpoint=endpoint.path,
                                depends_on=other_ep.path,
                                reason=f"Required param '{param}' from {other_ep.path}",
                                required_output=param
                            ))
                        break

        return dependencies
    
#     def _detect_llm_deps(self, schema, G: nx.DiGraph) -> List[Dependency]:

#     endpoint_list = "\n".join([
#         f"- {ep.method} {ep.path} (requires: {ep.required_params})"
#         for ep in schema.endpoints
#     ])

#     messages = [
#         {"role": "system", "content": "You are an API dependency analyzer. Find which endpoints must be called before others. Return ONLY valid JSON array. No explanation."},
#         {"role": "user", "content": f"""
# API: {schema.api_name}

# Endpoints:
# {endpoint_list}

# Return JSON array:
# [
#   {{
#     "endpoint": "/path",
#     "depends_on": "/other/path",
#     "reason": "why",
#     "required_output": "what value"
#   }}
# ]

# Empty array [] if no dependencies found.
# """}
#     ]

#     try:
#         raw = get_llm_response(messages=messages)
        
#         if "```" in raw:
#             parts = raw.split("```")
#             raw = parts[1] if len(parts) > 1 else raw
#             if raw.startswith("json"):
#                 raw = raw[4:]
#             raw = raw.split("```")[0]

#         deps_data = json.loads(raw.strip())
#         dependencies = []
#         valid_paths = {ep.path for ep in schema.endpoints}

#         for dep in deps_data:
#             ep_path = dep.get("endpoint", "")
#             dep_path = dep.get("depends_on", "")

#             if ep_path in valid_paths and dep_path in valid_paths:
#                 if not G.has_edge(dep_path, ep_path):
#                     G.add_edge(dep_path, ep_path, source="llm")

#                 dependencies.append(Dependency(
#                     endpoint=ep_path,
#                     depends_on=dep_path,
#                     reason=dep.get("reason", ""),
#                     required_output=dep.get("required_output", "")
#                 ))

#         print(f"   LLM found {len(dependencies)} additional deps")
#         return dependencies

#     except Exception as e:
#         print(f"   LLM detection failed: {e}")
#         return []
    def _detect_llm_deps(self, schema, G: nx.DiGraph) -> List[Dependency]:

        endpoint_list = "\n".join([
            f"- {ep.method} {ep.path} (requires: {ep.required_params})"
            for ep in schema.endpoints
        ])

        messages = [
            {"role": "system", "content": "You are an API dependency analyzer. Find which endpoints must be called before others. Return ONLY valid JSON array. No explanation."},
            {"role": "user", "content": f"API: {schema.api_name}\n\nEndpoints:\n{endpoint_list}\n\nReturn JSON array:\n[\n  {{\"endpoint\": \"/path\", \"depends_on\": \"/other/path\", \"reason\": \"why\", \"required_output\": \"what value\"}}\n]\n\nEmpty array [] if no dependencies found."}
        ]

        try:
            raw = get_llm_response(prompt=str(messages))

            if "```" in raw:
                parts = raw.split("```")
                raw = parts[1] if len(parts) > 1 else raw
                if raw.startswith("json"):
                    raw = raw[4:]
                raw = raw.split("```")[0]

            deps_data = json.loads(raw.strip())
            dependencies = []
            valid_paths = {ep.path for ep in schema.endpoints}

            for dep in deps_data:
                ep_path = dep.get("endpoint", "")
                dep_path = dep.get("depends_on", "")

                if ep_path in valid_paths and dep_path in valid_paths:
                    if not G.has_edge(dep_path, ep_path):
                        G.add_edge(dep_path, ep_path, source="llm")
                    dependencies.append(Dependency(
                        endpoint=ep_path,
                        depends_on=dep_path,
                        reason=dep.get("reason", ""),
                        required_output=dep.get("required_output", "")
                    ))

            print(f"   LLM found {len(dependencies)} additional deps")
            return dependencies

        except Exception as e:
            print(f"   LLM detection failed: {e}")
            return []