import logging

from confluent_kafka import KafkaException, Producer

from app.core.config import KAFKA_APPOINTMENTS_TOPIC, KAFKA_BOOTSTRAP_SERVERS
from app.schemas.event import AppointmentEvent

logger = logging.getLogger(__name__)

_producer: Producer | None = None


def get_producer() -> Producer | None:
    global _producer
    if not KAFKA_BOOTSTRAP_SERVERS:
        return None
    if _producer is None:
        _producer = Producer({"bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS})
    return _producer


def publish_appointment_event(event: AppointmentEvent) -> None:
    producer = get_producer()
    if producer is None:
        return
    try:
        producer.produce(
            KAFKA_APPOINTMENTS_TOPIC,
            key=str(event.appointment_id).encode(),
            value=event.model_dump_json().encode(),
        )
        remaining = producer.flush(2)
        if remaining > 0:
            logger.warning("kafka flush timed out publishing %s", event.event_type.value)
    except KafkaException:
        logger.exception("failed to publish %s", event.event_type.value)
    except Exception:
        logger.exception("failed to publish %s", event.event_type.value)
