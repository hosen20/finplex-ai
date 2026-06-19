from dataclasses import dataclass, field
from pathlib import Path


@dataclass(slots=True)
class EvidenceChunk:
    """Internal evidence chunk indexed by the hybrid retriever."""

    evidence_id: str
    source_type: str
    title: str
    content: str
    source_path: Path
    chunk_index: int
    metadata: dict[str, str] = field(default_factory=dict)

    def snippet(self, max_length: int = 280) -> str:
        clean_content = " ".join(self.content.split())

        if len(clean_content) <= max_length:
            return clean_content

        return f"{clean_content[:max_length].rstrip()}..."


@dataclass(slots=True)
class EvidenceMatch:
    """Search result with hybrid score details."""

    chunk: EvidenceChunk
    score: float
    sparse_score: float
    dense_score: float
    exact_match_score: float
    source_boost: float
    matched_terms: list[str] = field(default_factory=list)