from app.api.schemas.invoice import (
    InvoiceCreateRequest,
    InvoiceResponse,
    InvoiceUploadResponse,
)
from app.application.services.invoice_service import InvoiceService
from app.application.services.invoice_upload_service import InvoiceUploadService
from app.config import settings
from app.database import get_db_session
from app.dependencies import get_current_user
from app.infrastructure.db.models.user_model import UserModel
from app.infrastructure.messaging.event_publisher import (
    EventPublisher,
    get_event_publisher,
)
from app.infrastructure.storage.invoice_storage import (
    InvoiceStorage,
    get_invoice_storage,
)
from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from sqlalchemy.orm import Session

router = APIRouter(prefix="/invoices", tags=["invoices"])


@router.post("/upload", response_model=InvoiceUploadResponse)
async def upload_invoice(
    tenant_id: str = Form(...),
    customer_id: str | None = Form(None),
    file: UploadFile = File(...),
    current_user: UserModel = Depends(get_current_user),
    session: Session = Depends(get_db_session),
    storage: InvoiceStorage = Depends(get_invoice_storage),
    event_publisher: EventPublisher = Depends(get_event_publisher),
):
    service = InvoiceUploadService(
        session=session,
        storage=storage,
        event_publisher=event_publisher,
    )
    result = service.upload_invoice_file(
        tenant_id=tenant_id,
        actor_user_id=current_user.user_id,
        customer_id=customer_id,
        file_name=file.filename or "invoice.bin",
        content_type=file.content_type or "application/octet-stream",
        content=await file.read(),
    )

    return InvoiceUploadResponse(
        invoice=result.invoice,
        event_id=result.event.event_id,
        event_type=result.event.event_type,
        event_topic=settings.kafka_invoice_uploaded_topic,
    )


@router.post("", response_model=InvoiceResponse)
def create_invoice(
    payload: InvoiceCreateRequest,
    current_user: UserModel = Depends(get_current_user),
    session: Session = Depends(get_db_session),
):
    service = InvoiceService(session)
    return service.create_invoice_metadata(
        tenant_id=payload.tenant_id,
        actor_user_id=current_user.user_id,
        file_name=payload.file_name,
        storage_key=payload.storage_key,
        customer_id=payload.customer_id,
        extracted_fields=payload.extracted_fields,
    )


@router.get("", response_model=list[InvoiceResponse])
def list_invoices(
    tenant_id: str = Query(...),
    current_user: UserModel = Depends(get_current_user),
    session: Session = Depends(get_db_session),
):
    service = InvoiceService(session)
    return service.list_invoices(
        tenant_id=tenant_id,
        actor_user_id=current_user.user_id,
    )