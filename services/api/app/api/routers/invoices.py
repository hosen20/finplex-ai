from app.api.schemas.invoice import InvoiceCreateRequest, InvoiceResponse
from app.application.services.invoice_service import InvoiceService
from app.database import get_db_session
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

router = APIRouter(prefix="/invoices", tags=["invoices"])


@router.post("", response_model=InvoiceResponse)
def create_invoice(
    payload: InvoiceCreateRequest,
    session: Session = Depends(get_db_session),
):
    service = InvoiceService(session)
    return service.create_invoice_metadata(
        tenant_id=payload.tenant_id,
        actor_user_id=payload.actor_user_id,
        file_name=payload.file_name,
        storage_key=payload.storage_key,
        customer_id=payload.customer_id,
        extracted_fields=payload.extracted_fields,
    )


@router.get("", response_model=list[InvoiceResponse])
def list_invoices(
    tenant_id: str = Query(...),
    actor_user_id: str = Query(...),
    session: Session = Depends(get_db_session),
):
    service = InvoiceService(session)
    return service.list_invoices(
        tenant_id=tenant_id,
        actor_user_id=actor_user_id,
    )