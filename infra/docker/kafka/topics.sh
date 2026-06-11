#!/usr/bin/env bash
set -euo pipefail

BOOTSTRAP_SERVER="finplex-kafka:9092"

echo "Waiting for Kafka at ${BOOTSTRAP_SERVER}..."

for attempt in {1..30}; do
  if kafka-broker-api-versions --bootstrap-server "${BOOTSTRAP_SERVER}" >/dev/null 2>&1; then
    echo "Kafka is ready."
    break
  fi

  echo "Kafka not ready yet. Attempt ${attempt}/30..."
  sleep 2
done

create_topic() {
  local topic_name="$1"

  kafka-topics \
    --bootstrap-server "${BOOTSTRAP_SERVER}" \
    --create \
    --if-not-exists \
    --topic "${topic_name}" \
    --partitions 1 \
    --replication-factor 1

  echo "Ensured topic exists: ${topic_name}"
}

create_topic "invoice.uploaded"
create_topic "invoice.extracted"
create_topic "invoice.scored"
create_topic "invoice.drafted"
create_topic "invoice.reviewed"
create_topic "audit.events"

echo "Kafka topic initialization complete."