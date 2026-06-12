from app.api.schemas.tenant import (
    TenantActionRequest,
    TenantCreateRequest,
    TenantResponse,
)
from app.application.services.tenant_service import TenantService
from app.database import get_db_session
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

router = APIRouter(prefix="/tenants", tags=["tenants"])


@router.post("", response_model=TenantResponse)
def create_tenant(
    payload: TenantCreateRequest,
    session: Session = Depends(get_db_session),
):
    service = TenantService(session)
    return service.create_tenant(
        name=payload.name,
        erp_provider=payload.erp_provider,
        crm_provider=payload.crm_provider,
        actor_user_id=payload.actor_user_id,
    )


@router.get("", response_model=list[TenantResponse])
def list_tenants(session: Session = Depends(get_db_session)):
    service = TenantService(session)
    return service.list_tenants()


@router.post("/{tenant_id}/suspend", response_model=TenantResponse)
def suspend_tenant(
    tenant_id: str,
    payload: TenantActionRequest,
    session: Session = Depends(get_db_session),
):
    service = TenantService(session)
    return service.suspend_tenant(
        tenant_id=tenant_id,
        actor_user_id=payload.actor_user_id,
    )


@router.post("/{tenant_id}/reactivate", response_model=TenantResponse)
def reactivate_tenant(
    tenant_id: str,
    payload: TenantActionRequest,
    session: Session = Depends(get_db_session),
):
    service = TenantService(session)
    return service.reactivate_tenant(
        tenant_id=tenant_id,
        actor_user_id=payload.actor_user_id,
    )