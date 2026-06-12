import json
from typing import Protocol

from app.config import settings
from app.infrastructure.messaging.events import InvoiceUploadedEvent


class EventPublisher(Protocol):
    """Event publisher interface used by application services."""

    def publish_invoice_uploaded(self, event: InvoiceUploadedEvent) -> None:
        """Publish an invoice-uploaded event."""


class NoopEventPublisher:
    """Publisher used in tests when no broker is needed."""

    def publish_invoice_uploaded(self, event: InvoiceUploadedEvent) -> None:
        return None


class KafkaEventPublisher:
    """Publishes application events to Kafka."""

    def __init__(
        self,
        *,
        bootstrap_servers: str | None = None,
        topic: str | None = None,
    ) -> None:
        self.bootstrap_servers = bootstrap_servers or settings.kafka_bootstrap_servers
        self.topic = topic or settings.kafka_invoice_uploaded_topic
        self._producer = None

    def publish_invoice_uploaded(self, event: InvoiceUploadedEvent) -> None:
        producer = self._get_producer()
        producer.send(
            self.topic,
            key=event.invoice_id,
            value=event.to_dict(),
        )
        producer.flush(timeout=10)

    def _get_producer(self):
        if self._producer is None:
            from kafka import KafkaProducer

            self._producer = KafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                client_id=settings.kafka_client_id,
                value_serializer=lambda value: json.dumps(value).encode("utf-8"),
                key_serializer=lambda value: value.encode("utf-8"),
            )

        return self._producer


def get_event_publisher() -> EventPublisher:
    """FastAPI dependency that selects the configured event publisher."""
    if settings.event_publisher_backend == "noop":
        return NoopEventPublisher()

    return KafkaEventPublisher()