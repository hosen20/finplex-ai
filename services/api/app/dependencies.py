from collections.abc import Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.database import get_db_session
from app.domain.enums import UserRole
from app.infrastructure.db.models.user_model import UserModel
from app.infrastructure.db.repositories.user_repository import UserRepository
from app.security import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: Session = Depends(get_db_session),
) -> UserModel:
    payload = decode_access_token(token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if not isinstance(user_id, str):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token subject.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = UserRepository(session).get(user_id)

    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


def require_roles(*allowed_roles: UserRole) -> Callable[[UserModel], UserModel]:
    def dependency(
        current_user: UserModel = Depends(get_current_user),
    ) -> UserModel:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action.",
            )

        return current_user

    return dependency


def require_platform_admin(
    current_user: UserModel = Depends(get_current_user),
) -> UserModel:
    if current_user.role != UserRole.PLATFORM_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only platform admins can perform this action.",
        )

    return current_user


def resolve_tenant_scope(
    current_user: UserModel,
    requested_tenant_id: str | None = None,
    *,
    require_platform_tenant: bool = True,
) -> str:
    """Resolve the tenant a request is allowed to operate on.

    Tenant-facing API routes must not trust tenant_id values sent by the React
    app. Normal tenant users are always scoped to the tenant stored in their
    JWT-backed user record. Platform admins may specify a tenant_id for internal
    admin workflows such as creating the first tenant admin from Streamlit.
    """

    if current_user.role == UserRole.PLATFORM_ADMIN:
        if requested_tenant_id:
            return requested_tenant_id

        if require_platform_tenant:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Platform admin requests must include a tenant_id.",
            )

        return current_user.tenant_id

    if requested_tenant_id and requested_tenant_id != current_user.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot access another tenant's data.",
        )

    return current_user.tenant_id
