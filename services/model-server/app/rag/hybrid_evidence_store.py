from __future__ import annotations

import csv
import hashlib
import re
from pathlib import Path

from sklearn.decomposition import TruncatedSVD
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import normalize

from app.config import settings
from app.rag.documents import EvidenceChunk, EvidenceMatch

_TOKEN_PATTERN = re.compile(r"[a-zA-Z0-9_]+")


class HybridEvidenceStore:
    """Local hybrid RAG store for explainable evidence retrieval.

    The MVP uses local files instead of an external vector database. It combines:
    - sparse TF-IDF matching
    - dense SVD/LSA semantic vectors
    - exact keyword overlap
    - source-specific boosts
    """

    def __init__(
        self,
        *,
        regulations_dir: Path | None = None,
        seed_dir: Path | None = None,
        chunk_size_chars: int | None = None,
        sparse_weight: float | None = None,
        dense_weight: float | None = None,
        exact_match_weight: float | None = None,
        semantic_dimensions: int | None = None,
    ) -> None:
        self.regulations_dir = regulations_dir or settings.evidence_regulations_dir
        self.seed_dir = seed_dir or settings.evidence_seed_dir
        self.chunk_size_chars = (
            chunk_size_chars or settings.evidence_chunk_size_chars
        )
        self.sparse_weight = sparse_weight or settings.rag_sparse_weight
        self.dense_weight = dense_weight or settings.rag_dense_weight
        self.exact_match_weight = (
            exact_match_weight or settings.rag_exact_match_weight
        )
        self.semantic_dimensions = (
            semantic_dimensions or settings.rag_semantic_dimensions
        )

        self._chunks: list[EvidenceChunk] = []
        self._vectorizer: TfidfVectorizer | None = None
        self._tfidf_matrix = None
        self._svd: TruncatedSVD | None = None
        self._dense_matrix = None
        self._is_indexed = False

    def search(
        self,
        *,
        query: str,
        source_types: list[str] | None = None,
        top_k: int = 5,
    ) -> list[EvidenceMatch]:
        """Return top evidence matches for the query."""

        self._ensure_index()

        if not self._chunks or self._vectorizer is None:
            return []

        allowed_sources = set(source_types or [])
        query_tokens = self._tokens(query)
        query_vector = self._vectorizer.transform([query])

        sparse_scores = cosine_similarity(
            query_vector,
            self._tfidf_matrix,
        ).ravel()

        dense_scores = self._dense_scores(query_vector)

        matches: list[EvidenceMatch] = []
        for index, chunk in enumerate(self._chunks):
            if allowed_sources and chunk.source_type not in allowed_sources:
                continue

            exact_score = self._exact_match_score(query_tokens, chunk)
            source_boost = self._source_boost(chunk.source_type)
            sparse_score = float(sparse_scores[index])
            dense_score = float(dense_scores[index])

            combined_score = (
                (self.sparse_weight * sparse_score)
                + (self.dense_weight * dense_score)
                + (self.exact_match_weight * exact_score)
            )
            combined_score *= source_boost

            matched_terms = sorted(
                query_tokens.intersection(self._tokens(chunk.content))
            )

            if combined_score > 0:
                matches.append(
                    EvidenceMatch(
                        chunk=chunk,
                        score=round(combined_score, 6),
                        sparse_score=round(sparse_score, 6),
                        dense_score=round(dense_score, 6),
                        exact_match_score=round(exact_score, 6),
                        source_boost=source_boost,
                        matched_terms=matched_terms,
                    )
                )

        matches.sort(key=lambda item: item.score, reverse=True)

        if matches:
            return matches[:top_k]

        return self._fallback_matches(
            source_types=source_types or [],
            top_k=top_k,
        )

    def _ensure_index(self) -> None:
        if self._is_indexed:
            return

        self._chunks = [
            *self._load_regulation_chunks(),
            *self._load_seed_chunks(),
        ]

        if not self._chunks:
            self._is_indexed = True
            return

        corpus = [self._index_text(chunk) for chunk in self._chunks]
        self._vectorizer = TfidfVectorizer(
            lowercase=True,
            stop_words="english",
            ngram_range=(1, 2),
            min_df=1,
        )
        self._tfidf_matrix = self._vectorizer.fit_transform(corpus)
        self._fit_dense_index()
        self._is_indexed = True

    def _fit_dense_index(self) -> None:
        if self._tfidf_matrix is None:
            return

        row_count, feature_count = self._tfidf_matrix.shape
        max_components = min(
            self.semantic_dimensions,
            max(row_count - 1, 1),
            max(feature_count - 1, 1),
        )

        if max_components < 2:
            self._svd = None
            self._dense_matrix = None
            return

        self._svd = TruncatedSVD(
            n_components=max_components,
            random_state=42,
        )
        dense_matrix = self._svd.fit_transform(self._tfidf_matrix)
        self._dense_matrix = normalize(dense_matrix)

    def _dense_scores(self, query_vector) -> list[float]:
        if self._svd is None or self._dense_matrix is None:
            return [0.0 for _ in self._chunks]

        dense_query = self._svd.transform(query_vector)
        dense_query = normalize(dense_query)

        return cosine_similarity(dense_query, self._dense_matrix).ravel().tolist()

    def _load_regulation_chunks(self) -> list[EvidenceChunk]:
        if not self.regulations_dir.exists():
            return []

        paths = []
        for extension in ("*.md", "*.txt", "*.yaml", "*.yml"):
            paths.extend(self.regulations_dir.rglob(extension))

        chunks: list[EvidenceChunk] = []
        for path in sorted(paths):
            text = path.read_text(encoding="utf-8", errors="ignore")
            chunks.extend(
                self._chunk_text(
                    path=path,
                    source_type="regulation",
                    title=self._title_from_text(path, text),
                    text=text,
                )
            )

        return chunks

    def _load_seed_chunks(self) -> list[EvidenceChunk]:
        if not self.seed_dir.exists():
            return []

        chunks: list[EvidenceChunk] = []
        for path in sorted(self.seed_dir.glob("*.csv")):
            source_type = self._source_type_from_seed_path(path)
            title = path.stem.replace("_", " ").title()
            text = self._csv_to_text(path)

            chunks.extend(
                self._chunk_text(
                    path=path,
                    source_type=source_type,
                    title=title,
                    text=text,
                )
            )

        return chunks

    def _chunk_text(
        self,
        *,
        path: Path,
        source_type: str,
        title: str,
        text: str,
    ) -> list[EvidenceChunk]:
        clean_text = text.strip()
        if not clean_text:
            return []

        overlap_chars = min(120, max(self.chunk_size_chars // 5, 0))
        step_size = max(self.chunk_size_chars - overlap_chars, 1)

        chunks: list[EvidenceChunk] = []
        for index, start in enumerate(range(0, len(clean_text), step_size)):
            content = clean_text[start : start + self.chunk_size_chars].strip()
            if not content:
                continue

            evidence_id = self._evidence_id(path, index)
            chunks.append(
                EvidenceChunk(
                    evidence_id=evidence_id,
                    source_type=source_type,
                    title=title,
                    content=content,
                    source_path=path,
                    chunk_index=index,
                    metadata={
                        "path": str(path),
                        "chunk_index": str(index),
                        "retrieval_method": "hybrid_sparse_dense_local",
                    },
                )
            )

            if start + self.chunk_size_chars >= len(clean_text):
                break

        return chunks

    def _fallback_matches(
        self,
        *,
        source_types: list[str],
        top_k: int,
    ) -> list[EvidenceMatch]:
        allowed_sources = set(source_types)
        chunks = self._chunks

        if allowed_sources:
            chunks = [
                chunk
                for chunk in chunks
                if chunk.source_type in allowed_sources
            ]

        fallback_chunks = sorted(
            chunks,
            key=lambda chunk: self._source_boost(chunk.source_type),
            reverse=True,
        )[:top_k]

        return [
            EvidenceMatch(
                chunk=chunk,
                score=0.01,
                sparse_score=0.0,
                dense_score=0.0,
                exact_match_score=0.0,
                source_boost=self._source_boost(chunk.source_type),
                matched_terms=[],
            )
            for chunk in fallback_chunks
        ]

    def _index_text(self, chunk: EvidenceChunk) -> str:
        metadata_text = " ".join(
            f"{key} {value}" for key, value in chunk.metadata.items()
        )
        return (
            f"{chunk.source_type} {chunk.title} "
            f"{metadata_text} {chunk.content}"
        )

    def _exact_match_score(
        self,
        query_tokens: set[str],
        chunk: EvidenceChunk,
    ) -> float:
        if not query_tokens:
            return 0.0

        chunk_tokens = self._tokens(
            f"{chunk.title} {chunk.source_type} {chunk.content}"
        )
        matched_count = len(query_tokens.intersection(chunk_tokens))

        return matched_count / len(query_tokens)

    def _source_boost(self, source_type: str) -> float:
        return {
            "regulation": 1.25,
            "invoice": 1.2,
            "erp": 1.15,
            "crm": 1.15,
        }.get(source_type, 1.0)

    def _tokens(self, text: str) -> set[str]:
        return {
            token.lower()
            for token in _TOKEN_PATTERN.findall(text)
            if len(token) >= 3
        }

    def _csv_to_text(self, path: Path) -> str:
        try:
            with path.open("r", encoding="utf-8", errors="ignore") as file_obj:
                reader = csv.DictReader(file_obj)
                rows = []
                for index, row in enumerate(reader):
                    if index >= 80:
                        break

                    row_text = ", ".join(
                        f"{key}: {value}"
                        for key, value in row.items()
                        if value not in {None, ""}
                    )
                    rows.append(row_text)
        except csv.Error:
            return path.read_text(encoding="utf-8", errors="ignore")

        return "\n".join(rows)

    def _title_from_text(self, path: Path, text: str) -> str:
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith("#"):
                return stripped.lstrip("#").strip()

        return path.stem.replace("_", " ").title()

    def _source_type_from_seed_path(self, path: Path) -> str:
        name = path.name.lower()

        if "crm" in name or "customer" in name:
            return "crm"

        if "erp" in name or "payment" in name:
            return "erp"

        if "invoice" in name:
            return "invoice"

        return "rag"

    def _evidence_id(self, path: Path, chunk_index: int) -> str:
        raw_id = f"{path}:{chunk_index}".encode()
        digest = hashlib.sha1(raw_id).hexdigest()[:16]
        return f"ev_{digest}"