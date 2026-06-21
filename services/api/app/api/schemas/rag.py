from pydantic import BaseModel, Field


class RagSearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=1000)
    limit: int = Field(default=5, ge=1, le=20)


class RagEvidenceResponse(BaseModel):
    chunk_id: str
    document_id: str
    document_title: str
    source_type: str
    content: str
    score: float


class RagSearchResponse(BaseModel):
    tenant_id: str
    query: str
    results: list[RagEvidenceResponse]
