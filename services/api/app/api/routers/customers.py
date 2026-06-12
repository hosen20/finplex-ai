from app.api.schemas.customer import CustomerCreateRequest, CustomerResponse
from app.application.services.customer_service import CustomerService
from app.database import get_db_session
from app.dependencies import get_current_user
from app.infrastructure.db.models.user_model import UserModel
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

router = APIRouter(prefix="/customers", tags=["customers"])


@router.post("", response_model=CustomerResponse)
def create_customer(
    payload: CustomerCreateRequest,
    current_user: UserModel = Depends(get_current_user),
    session: Session = Depends(get_db_session),
):
    service = CustomerService(session)
    return service.create_customer(
        tenant_id=payload.tenant_id,
        actor_user_id=current_user.user_id,
        company_name=payload.company_name,
        contact_name=payload.contact_name,
        contact_email=payload.contact_email,
        preferred_contact_channel=payload.preferred_contact_channel,
        relationship_status=payload.relationship_status,
        tags=payload.tags,
    )


@router.get("", response_model=list[CustomerResponse])
def list_customers(
    tenant_id: str = Query(...),
    current_user: UserModel = Depends(get_current_user),
    session: Session = Depends(get_db_session),
):
    service = CustomerService(session)
    return service.list_customers(
        tenant_id=tenant_id,
        actor_user_id=current_user.user_id,
    )