from app.domain.entities.invoice import Invoice
from app.domain.entities.review import Review
from app.domain.entities.tenant import Tenant
from app.domain.entities.user import User
from app.infrastructure.db.models.invoice_model import InvoiceModel
from app.infrastructure.db.models.review_model import ReviewModel
from app.infrastructure.db.models.tenant_model import TenantModel
from app.infrastructure.db.models.user_model import UserModel


def tenant_model_to_domain(model: TenantModel) -> Tenant:
    return Tenant(
        tenant_id=model.tenant_id,
        name=model.name,
        status=model.status,
        erp_provider=model.erp_provider,
        crm_provider=model.crm_provider,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def user_model_to_domain(model: UserModel) -> User:
    return User(
        user_id=model.user_id,
        tenant_id=model.tenant_id,
        email=model.email,
        full_name=model.full_name,
        role=model.role,
        is_active=model.is_active,
        created_at=model.created_at,
    )


def invoice_model_to_domain(model: InvoiceModel) -> Invoice:
    return Invoice(
        invoice_id=model.invoice_id,
        tenant_id=model.tenant_id,
        uploaded_by_user_id=model.uploaded_by_user_id,
        file_name=model.file_name,
        storage_key=model.storage_key,
        customer_id=model.customer_id,
        status=model.status,
        payment_status=model.payment_status,
        extracted_fields=None,
        evidence_ids=model.evidence_ids or [],
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def review_model_to_domain(model: ReviewModel) -> Review:
    return Review(
        review_id=model.review_id,
        tenant_id=model.tenant_id,
        invoice_id=model.invoice_id,
        draft_message=model.draft_message,
        risk_level=model.risk_level,
        guardrails_passed=model.guardrails_passed,
        evidence_ids=model.evidence_ids or [],
        status=model.status,
        reviewer_user_id=model.reviewer_user_id,
        reviewer_comment=model.reviewer_comment,
        created_at=model.created_at,
        decided_at=model.updated_at,
    )