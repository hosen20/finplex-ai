import json
from collections.abc import Callable
from typing import Any

from app.config import settings
from app.events import InvoiceUploadedEvent


class KafkaInvoiceUploadedConsumer:
    """Consumes invoice.uploaded events and passes them to a handler."""

    def __init__(
        self,
        *,
        event_handler: Callable[[InvoiceUploadedEvent], None],
        bootstrap_servers: str | None = None,
        topic: str | None = None,
        group_id: str | None = None,
    ) -> None:
        self.event_handler = event_handler
        self.bootstrap_servers = bootstrap_servers or settings.kafka_bootstrap_servers
        self.topic = topic or settings.kafka_invoice_uploaded_topic
        self.group_id = group_id or settings.kafka_consumer_group_id
        self._consumer: Any | None = None

    def run_forever(self) -> None:
        consumer = self._get_consumer()
        print(
            {
                "service": settings.app_name,
                "status": "consuming",
                "topic": self.topic,
                "group_id": self.group_id,
            },
            flush=True,
        )

        for message in consumer:
            event = InvoiceUploadedEvent.model_validate(message.value)
            self.event_handler(event)

    def close(self) -> None:
        if self._consumer is not None:
            self._consumer.close()

    def _get_consumer(self) -> Any:
        if self._consumer is None:
            from kafka import KafkaConsumer

            self._consumer = KafkaConsumer(
                self.topic,
                bootstrap_servers=self.bootstrap_servers,
                group_id=self.group_id,
                client_id=settings.kafka_client_id,
                auto_offset_reset=settings.kafka_auto_offset_reset,
                enable_auto_commit=True,
                value_deserializer=self._deserialize_json,
            )

        return self._consumer

    def _deserialize_json(self, value: bytes) -> dict[str, Any]:
        return json.loads(value.decode("utf-8"))