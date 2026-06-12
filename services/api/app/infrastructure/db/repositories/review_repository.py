from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.enums import ReviewStatus
from app.infrastructure.db.models.review_model import ReviewModel
from app.infrastructure.db.repositories.base_repository import BaseRepository


class ReviewRepository(BaseRepository[ReviewModel]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, ReviewModel)

    def get(self, review_id: str) -> ReviewModel | None:
        return self.get_by_id(review_id)

    def list_pending_by_tenant(self, tenant_id: str) -> list[ReviewModel]:
        statement = select(ReviewModel).where(
            ReviewModel.tenant_id == tenant_id,
            ReviewModel.status == ReviewStatus.PENDING,
        )
        return list(self.session.scalars(statement).all())