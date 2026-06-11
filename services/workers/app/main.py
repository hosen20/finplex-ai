import time

from app.config import settings


def main() -> None:
    """Run a lightweight local worker loop until Kafka consumption is implemented."""
    print(
        {
            "service": settings.app_name,
            "status": "running",
            "environment": settings.environment,
            "kafka": settings.kafka_bootstrap_servers,
            "topic": settings.kafka_invoice_uploaded_topic,
        },
        flush=True,
    )

    while True:
        time.sleep(30)
        print(
            {
                "service": settings.app_name,
                "status": "waiting_for_invoice_events",
                "topic": settings.kafka_invoice_uploaded_topic,
            },
            flush=True,
        )


if __name__ == "__main__":
    main()