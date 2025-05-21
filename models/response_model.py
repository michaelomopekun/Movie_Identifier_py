from pydantic import BaseModel
from typing import Dict, Any

class SearchResult(BaseModel):
    id: str
    document: str
    metadata: Dict[str, Any]
    distance: float
