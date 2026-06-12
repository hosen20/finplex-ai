from sqlalchemy import select
from sqlalchemy.orm import Session

from app.infrastructure.db.models.user_model import UserModel
from app.infrastructure.db.repositories.base_repository import BaseRepository


class UserRepository(BaseRepository[UserModel]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, UserModel)

    def get(self, user_id: str) -> UserModel | None:
        return self.get_by_id(user_id)

    def get_by_email(self, email: str) -> UserModel | None:
        statement = select(UserModel).where(UserModel.email == email)
        return self.session.scalar(statement)

    def list_by_tenant(self, tenant_id: str) -> list[UserModel]:
        statement = select(UserModel).where(UserModel.tenant_id == tenant_id)
        return list(self.session.scalars(statement).all())