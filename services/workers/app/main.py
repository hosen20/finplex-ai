from app.clients.guardrails_client import GuardrailsClient
from app.clients.model_server_client import ModelServerClient
from app.config import settings
from app.events import InvoiceUploadedEvent
from app.kafka_consumer import KafkaInvoiceUploadedConsumer
from app.repositories import InvoiceProcessingRepository, SessionLocal
from app.services.invoice_processing_service import InvoiceProcessingService
from app.storage import LocalInvoiceTextReader


def handle_invoice_uploaded(event: InvoiceUploadedEvent) -> None:
    """Process one invoice-uploaded event inside its own database session."""
    with SessionLocal() as session:
        repository = InvoiceProcessingRepository(session)
        model_client = ModelServerClient()
        guardrails_client = GuardrailsClient()
        text_reader = LocalInvoiceTextReader()

        service = InvoiceProcessingService(
            repository=repository,
            model_client=model_client,
            guardrails_client=guardrails_client,
            text_reader=text_reader,
        )
        review_id = service.process_event(event)

        print(
            {
                "service": settings.app_name,
                "status": "invoice_processed",
                "invoice_id": event.invoice_id,
                "review_id": review_id,
            },
            flush=True,
        )


def main() -> None:
    """Run the local Kafka invoice worker."""
    consumer = KafkaInvoiceUploadedConsumer(
        event_handler=handle_invoice_uploaded,
    )

    try:
        consumer.run_forever()
    finally:
        consumer.close()


if __name__ == "__main__":
    main()