from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass(slots=True)
class Customer:
    customer_id: str
    tenant_id: str
    company_name: str
    contact_name: str
    contact_email: str
    preferred_contact_channel: str = "email"
    relationship_status: str = "normal"
    tags: list[str] = field(default_factory=list)
    created_at: datetime = datetime.now(UTC)

    def has_tag(self, tag: str) -> bool:
        return tag.lower() in {item.lower() for item in self.tags}

    @property
    def has_risk_flag(self) -> bool:
        risk_tags = {"dispute", "high_risk", "late_payer", "legal_review"}
        return bool(risk_tags.intersection({tag.lower() for tag in self.tags}))