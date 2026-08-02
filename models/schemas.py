# models/schemas.py
# Ye file poore project mein use hogi
# Har agent inhi models ko input/output dega

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

# ═══════════════════════════════════════════
# LEVEL 1: Single Endpoint
# ═══════════════════════════════════════════

class EndpointSchema(BaseModel):

    method: str
    # str type enforce hoga — "GET", "POST" etc.

    path: str
    # "/pet", "/user/{userId}"

    description: str = ""
    # = "" kyun? Default value
    # Agar LLM ne ye field nahi diya →
    # ValidationError ki jagah empty string milegi

    required_params: List[str] = []
    # Default empty list
    # = [] directly nahi likh sakte Pydantic mein?
    # Pydantic mein likh SAKTE hain — ye Pydantic v2 hai
    # Pydantic v1 mein Field(default_factory=list) chahiye tha

    optional_params: List[str] = []

    param_types: Dict[str, str] = {}
    # {"name": "string", "petId": "integer"}
    # Key = param naam, Value = type

    auth_required: bool = False

    auth_type: Optional[str] = None
    # Optional[str] = Union[str, None]
    # Matlab: ya toh string hai ya None
    # None = auth type documented nahi

    rate_limit: Optional[str] = None

    response_schema: Dict[str, Any] = {}
    # Any kyun? Response structure
    # nested aur complex ho sakti hai
    # strict typing difficult hai yahan

    error_codes: List[Dict] = []
    # [{"code": 404, "meaning": "Not found"}]

    example_request: Optional[str] = None
    example_response: Optional[str] = None


# ═══════════════════════════════════════════
# LEVEL 2: Poori API
# ═══════════════════════════════════════════

class APISchema(BaseModel):

    api_name: str

    base_url: str

    auth_method: str = "None"
    # "None" string hai, Python None nahi
    # Report mein "None" print hoga, "null" nahi

    auth_instructions: str = ""

    global_headers: Dict[str, str] = {}

    rate_limits: str = "Not specified"

    endpoints: List[EndpointSchema] = []
    # Nested Pydantic models!
    # Pydantic automatically validate karta hai
    # Har endpoint EndpointSchema format mein hona chahiye

    total_endpoints: int = 0

    api_version: str = ""

    def summary(self) -> str:
        """
        Instance method — object pe directly call karo
        schema.summary() → formatted string
        """
        return (
            f"API: {self.api_name}\n"
            f"Base URL: {self.base_url}\n"
            f"Auth: {self.auth_method}\n"
            f"Endpoints: {self.total_endpoints}\n"
            f"Rate Limits: {self.rate_limits}"
        )