from typing import Generic, TypeVar

from sqlalchemy.orm import Session

ModelT = TypeVar("ModelT")


class BaseRepository(Generic[ModelT]):
    """Small shared repository helper for SQLAlchemy models."""

    def __init__(self, session: Session, model: type[ModelT]) -> None:
        self.session = session
        self.model = model

    def add(self, instance: ModelT) -> ModelT:
        self.session.add(instance)
        self.session.flush()
        return instance

    def get_by_id(self, primary_key: str) -> ModelT | None:
        return self.session.get(self.model, primary_key)

    def delete(self, instance: ModelT) -> None:
        self.session.delete(instance)
        self.session.flush()