from app.api.schemas.user import UserCreateRequest, UserResponse
from app.application.services.user_service import UserService
from app.database import get_db_session
from app.dependencies import get_current_user, resolve_tenant_scope
from app.infrastructure.db.models.user_model import UserModel
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

router = APIRouter(prefix="/users", tags=["users"])


@router.post("", response_model=UserResponse)
def create_user(
    payload: UserCreateRequest,
    current_user: UserModel = Depends(get_current_user),
    session: Session = Depends(get_db_session),
):
    tenant_id = resolve_tenant_scope(current_user, payload.tenant_id)
    service = UserService(session)
    return service.create_user(
        tenant_id=tenant_id,
        email=payload.email,
        full_name=payload.full_name,
        password=payload.password,
        role=payload.role,
        actor_user_id=current_user.user_id,
    )


@router.get("", response_model=list[UserResponse])
def list_users(
    tenant_id: str | None = Query(None),
    current_user: UserModel = Depends(get_current_user),
    session: Session = Depends(get_db_session),
):
    resolved_tenant_id = resolve_tenant_scope(current_user, tenant_id)
    service = UserService(session)
    return service.list_users(
        tenant_id=resolved_tenant_id,
        actor_user_id=current_user.user_id,
    )
