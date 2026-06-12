from app.api.schemas.customer import CustomerCreateRequest, CustomerResponse
from app.application.services.customer_service import CustomerService
from app.database import get_db_session
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

router = APIRouter(prefix="/customers", tags=["customers"])


@router.post("", response_model=CustomerResponse)
def create_customer(
    payload: CustomerCreateRequest,
    session: Session = Depends(get_db_session),
):
    service = CustomerService(session)
    return service.create_customer(
        tenant_id=payload.tenant_id,
        actor_user_id=payload.actor_user_id,
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
    actor_user_id: str = Query(...),
    session: Session = Depends(get_db_session),
):
    service = CustomerService(session)
    return service.list_customers(
        tenant_id=tenant_id,
        actor_user_id=actor_user_id,
    )