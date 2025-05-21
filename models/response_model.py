from pydantic import BaseModel

class SearchResult(BaseModel):
    id: str
    document: str
    metadata: dict
    distance: float
