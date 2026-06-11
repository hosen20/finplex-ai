class DomainError(Exception):
    """Base exception for domain-level errors."""


class TenantSuspendedError(DomainError):
    """Raised when an operation is attempted for a suspended tenant."""


class TenantDeletedError(DomainError):
    """Raised when an operation is attempted for a deleted tenant."""


class CrossTenantAccessError(DomainError):
    """Raised when data from one tenant is accessed by another tenant."""


class PermissionDeniedError(DomainError):
    """Raised when a user role cannot perform an action."""


class InvalidStateTransitionError(DomainError):
    """Raised when an entity is moved to an invalid state."""


class MissingEvidenceError(DomainError):
    """Raised when an AI decision lacks required supporting evidence."""


class GuardrailViolationError(DomainError):
    """Raised when a generated draft violates guardrail rules."""