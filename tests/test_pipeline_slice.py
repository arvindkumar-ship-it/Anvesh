import ast
import json
from types import SimpleNamespace

from backend.agents.schema_extractor import SchemaExtractorAgent
from backend.agents.dependency_mapper import DependencyMapperAgent
from backend.agents import code_generator


def test_openapi_to_dependencies_to_generated_code(monkeypatch):
    openapi = {'openapi': '3.0.0', 'info': {'title': 'Fixture API', 'version': '1.0'}, 'servers': [{'url': 'https://fixture.invalid'}], 'paths': {'/users': {'post': {'summary': 'Create user', 'responses': {'201': {'description': 'created'}}}}, '/users/{userId}': {'get': {'summary': 'Get user', 'parameters': [{'name': 'userId', 'in': 'path', 'required': True, 'schema': {'type': 'string'}}], 'responses': {'200': {'description': 'ok'}}}}}}
    document = SimpleNamespace(format_type='openapi', raw_text=json.dumps(openapi), openapi_data=openapi, structured_data=openapi, raw_json=openapi, url='https://fixture.invalid/openapi.json', raw_content=openapi, content=openapi, title='Fixture API')
    schema = SchemaExtractorAgent(None).extract(document)
    assert schema.total_endpoints == 2
    mapper = DependencyMapperAgent(None)
    monkeypatch.setattr(mapper, '_detect_llm_deps', lambda schema, graph: [])
    dependencies = mapper.map(schema)
    assert dependencies.execution_order.index('/users') < dependencies.execution_order.index('/users/{userId}')
    calls = []
    def generate(prompt, **kwargs):
        calls.append(str(prompt))
        return '```python\ndef generated_client():\n    return {"status": "fixture"}\n```'
    monkeypatch.setattr(code_generator, 'get_llm_response', generate)
    result = code_generator.CodeGeneratorAgent().generate(schema, dependencies, [], 'Create a user then fetch it')
    ast.parse(result.code)
    assert '/users' in calls[0]
    assert result.execution_order == dependencies.execution_order
