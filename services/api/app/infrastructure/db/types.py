"""Custom SQLAlchemy database types used by Finplex AI."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from sqlalchemy.types import UserDefinedType


class PgVectorType(UserDefinedType):
    """Minimal pgvector type without adding another runtime dependency.

    PostgreSQL receives vectors as strings like ``[0.1,0.2]``. SQLite accepts
    the column type during unit tests, so repository tests can still build the
    metadata in memory without a pgvector extension.
    """

    cache_ok = True

    def __init__(self, dimensions: int) -> None:
        self.dimensions = dimensions

    def get_col_spec(self, **_kwargs: Any) -> str:
        return f"vector({self.dimensions})"

    def bind_processor(self, _dialect: Any):  # type: ignore[no-untyped-def]
        def process(value: Sequence[float] | str | None) -> str | None:
            if value is None:
                return None
            if isinstance(value, str):
                return value
            return format_pgvector(value)

        return process

    def result_processor(  # type: ignore[no-untyped-def]
        self,
        _dialect: Any,
        _coltype: Any,
    ):
        def process(value: Any) -> list[float] | None:
            if value is None:
                return None
            if isinstance(value, list):
                return [float(item) for item in value]
            if isinstance(value, str):
                stripped = value.strip().strip("[]")
                if not stripped:
                    return []
                return [float(item) for item in stripped.split(",")]
            return value

        return process


def format_pgvector(values: Sequence[float]) -> str:
    """Convert a float sequence to pgvector's text input format."""

    return "[" + ",".join(f"{float(value):.6f}" for value in values) + "]"
