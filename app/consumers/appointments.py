import logging
import time

from confluent_kafka import Consumer, KafkaError, KafkaException

from app.core.config import (
    KAFKA_APPOINTMENTS_TOPIC,
    KAFKA_BOOTSTRAP_SERVERS,
    KAFKA_CONSUMER_GROUP,
    REDIS_URL,
)
from app.schemas.event import AppointmentEvent
from app.tasks.analytics import record_analytics
from app.tasks.notifications import send_notification

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _connect() -> Consumer:
    while True:
        if not KAFKA_BOOTSTRAP_SERVERS:
            logger.warning("KAFKA_BOOTSTRAP_SERVERS is not set, retrying...")
            time.sleep(2)
            continue
        try:
            consumer = Consumer(
                {
                    "bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS,
                    "group.id": KAFKA_CONSUMER_GROUP,
                    "auto.offset.reset": "earliest",
                    "enable.auto.commit": False,
                }
            )
            consumer.list_topics(timeout=5)
            logger.info("Connected to Kafka at %s", KAFKA_BOOTSTRAP_SERVERS)
            return consumer
        except KafkaException:
            logger.warning("Kafka not ready at %s, retrying...", KAFKA_BOOTSTRAP_SERVERS)
            time.sleep(2)


def _enqueue(event: AppointmentEvent) -> None:
    while True:
        if not REDIS_URL:
            logger.warning("REDIS_URL is not set, retrying enqueue...")
            time.sleep(2)
            continue
        try:
            payload = event.model_dump(mode="json")
            send_notification.delay(payload)
            record_analytics.delay(payload)
            return
        except Exception:
            logger.exception("failed to enqueue appointment event tasks, retrying...")
            time.sleep(2)


def main() -> None:
    consumer = _connect()
    consumer.subscribe([KAFKA_APPOINTMENTS_TOPIC])
    logger.info("Consumer listening on %s", KAFKA_APPOINTMENTS_TOPIC)
    try:
        while True:
            message = consumer.poll(1.0)
            if message is None:
                continue
            if message.error():
                if message.error().code() in (
                    KafkaError._PARTITION_EOF,
                    KafkaError.UNKNOWN_TOPIC_OR_PART,
                ):
                    continue
                logger.error("Kafka consumer error: %s", message.error())
                continue
            try:
                event = AppointmentEvent.model_validate_json(message.value())
                logger.info("received appointment event %s", event.model_dump(mode="json"))
                _enqueue(event)
                consumer.commit(message)
            except Exception:
                logger.exception("failed to parse appointment event: %s", message.value())
    finally:
        consumer.close()


if __name__ == "__main__":
    main()
