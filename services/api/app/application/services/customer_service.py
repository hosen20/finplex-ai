from uuid import uuid4

from app.application.services.audit_service import AuditService
from app.application.services.mappers import (
    tenant_model_to_domain,
    user_model_to_domain,
)
from app.domain.enums import AuditAction
from app.domain.policies.tenant_policy import TenantPolicy
from app.infrastructure.db.models.customer_model import CustomerModel
from app.infrastructure.db.repositories.customer_repository import CustomerRepository
from app.infrastructure.db.repositories.tenant_repository import TenantRepository
from app.infrastructure.db.repositories.user_repository import UserRepository
from sqlalchemy.orm import Session


class CustomerService:
    """Application workflows for tenant customers."""

    def __init__(self, session: Session) -> None:
        self.session = session
        self.customers = CustomerRepository(session)
        self.tenants = TenantRepository(session)
        self.users = UserRepository(session)
        self.audit = AuditService(session)

    def create_customer(
        self,
        *,
        tenant_id: str,
        actor_user_id: str,
        company_name: str,
        contact_name: str,
        contact_email: str,
        preferred_contact_channel: str = "email",
        relationship_status: str = "normal",
        tags: list[str] | None = None,
    ) -> CustomerModel:
        tenant = self.tenants.get(tenant_id)
        actor = self.users.get(actor_user_id)

        if tenant is None:
            raise ValueError(f"Tenant {tenant_id} was not found.")
        if actor is None:
            raise ValueError(f"User {actor_user_id} was not found.")

        TenantPolicy.ensure_tenant_is_active(tenant_model_to_domain(tenant))
        TenantPolicy.ensure_can_manage_tenant(user_model_to_domain(actor), tenant_id)

        customer = CustomerModel(
            customer_id=f"cust_{uuid4().hex}",
            tenant_id=tenant_id,
            company_name=company_name,
            contact_name=contact_name,
            contact_email=contact_email,
            preferred_contact_channel=preferred_contact_channel,
            relationship_status=relationship_status,
            tags=tags or [],
        )
        self.customers.add(customer)

        self.audit.record(
            tenant_id=tenant_id,
            action=AuditAction.USER_CREATED,
            actor_user_id=actor_user_id,
            entity_type="customer",
            entity_id=customer.customer_id,
            metadata={"company_name": company_name},
        )

        self.session.commit()
        return customer

    def list_customers(
        self,
        *,
        tenant_id: str,
        actor_user_id: str,
    ) -> list[CustomerModel]:
        actor = self.users.get(actor_user_id)

        if actor is None:
            raise ValueError(f"User {actor_user_id} was not found.")

        TenantPolicy.ensure_same_tenant(user_model_to_domain(actor), tenant_id)
        return self.customers.list_by_tenant(tenant_id)