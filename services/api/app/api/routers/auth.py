from app.api.schemas.auth import (
    AuthenticatedUserResponse,
    BootstrapAdminRequest,
    LoginRequest,
    TokenResponse,
)
from app.application.services.auth_service import AuthService
from app.database import get_db_session
from app.dependencies import get_current_user
from app.infrastructure.db.models.user_model import UserModel
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(
    payload: LoginRequest,
    session: Session = Depends(get_db_session),
):
    service = AuthService(session)
    user = service.authenticate_user(
        email=payload.email,
        password=payload.password,
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    return TokenResponse(access_token=service.create_token_for_user(user))


@router.get("/me", response_model=AuthenticatedUserResponse)
def get_me(current_user: UserModel = Depends(get_current_user)):
    return current_user


@router.post("/bootstrap-admin", response_model=AuthenticatedUserResponse)
def bootstrap_admin(
    payload: BootstrapAdminRequest,
    session: Session = Depends(get_db_session),
):
    raise HTTPException(
        status_code=status.HTTP_410_GONE,
        detail=(
            "Unauthenticated tenant bootstrap is disabled. Use "
            "scripts/bootstrap-platform-admin.py and create tenants from the "
            "Streamlit Platform Admin app."
        ),
    )
