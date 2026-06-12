from app.infrastructure.db.models.user_model import UserModel
from app.infrastructure.db.repositories.user_repository import UserRepository
from app.security import create_access_token, verify_password
from sqlalchemy.orm import Session


class AuthService:
    """Authentication workflow for login and token issuing."""

    def __init__(self, session: Session) -> None:
        self.session = session
        self.users = UserRepository(session)

    def authenticate_user(self, *, email: str, password: str) -> UserModel | None:
        user = self.users.get_by_email(email)

        if user is None:
            return None

        if not user.is_active:
            return None

        if not verify_password(password, user.hashed_password):
            return None

        return user

    def create_token_for_user(self, user: UserModel) -> str:
        return create_access_token(
            subject=user.user_id,
            tenant_id=user.tenant_id,
            role=user.role.value,
        )