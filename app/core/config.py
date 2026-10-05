import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


def _require(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"{name} is not set")
    return value


DATABASE_URL = _require("DATABASE_URL")
SECRET_KEY = _require("SECRET_KEY")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
TEMPORAL_ADDRESS = os.getenv("TEMPORAL_ADDRESS", "localhost:7233")
TEMPORAL_TASK_QUEUE = os.getenv("TEMPORAL_TASK_QUEUE", "smarthealth-task-queue")
BOOKING_HOLD_SECONDS = int(os.getenv("BOOKING_HOLD_SECONDS", "60"))
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "")
KAFKA_APPOINTMENTS_TOPIC = os.getenv("KAFKA_APPOINTMENTS_TOPIC", "appointments")
KAFKA_CONSUMER_GROUP = os.getenv("KAFKA_CONSUMER_GROUP", "smarthealth-appointments-logger")
REDIS_URL = os.getenv("REDIS_URL", "")
OTEL_EXPORTER_OTLP_ENDPOINT = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "")
OTEL_SERVICE_NAME = os.getenv("OTEL_SERVICE_NAME", "smarthealth-api")
CELERY_METRICS_PORT = int(os.getenv("CELERY_METRICS_PORT", "9000"))
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
EMBEDDING_DIM = int(os.getenv("EMBEDDING_DIM", "1536"))
EMBEDDING_BATCH_SIZE = int(os.getenv("EMBEDDING_BATCH_SIZE", "100"))
KNOWLEDGE_DIR = os.getenv(
    "KNOWLEDGE_DIR",
    str(Path(__file__).resolve().parents[2] / "data" / "knowledge"),
)
KNOWLEDGE_CHUNK_SIZE = int(os.getenv("KNOWLEDGE_CHUNK_SIZE", "800"))
KNOWLEDGE_CHUNK_OVERLAP = int(os.getenv("KNOWLEDGE_CHUNK_OVERLAP", "100"))
CHAT_MODEL = os.getenv("CHAT_MODEL", "gpt-4o-mini")
LLM_TIMEOUT_SECONDS = float(os.getenv("LLM_TIMEOUT_SECONDS", "30"))
RETRIEVAL_TOP_K = int(os.getenv("RETRIEVAL_TOP_K", "4"))
RETRIEVAL_MAX_DISTANCE = float(os.getenv("RETRIEVAL_MAX_DISTANCE", "0.7"))
CLINIC_TIMEZONE = os.getenv("CLINIC_TIMEZONE", "Asia/Karachi")
CLINIC_OPEN = os.getenv("CLINIC_OPEN", "09:00")
CLINIC_CLOSE = os.getenv("CLINIC_CLOSE", "17:00")
CLINIC_DAYS = os.getenv("CLINIC_DAYS", "0,1,2,3,4")
SLOT_MINUTES = int(os.getenv("SLOT_MINUTES", "30"))
ASSISTANT_MAX_RANGE_DAYS = int(os.getenv("ASSISTANT_MAX_RANGE_DAYS", "14"))
ASSISTANT_MAX_APPOINTMENTS = int(os.getenv("ASSISTANT_MAX_APPOINTMENTS", "10"))
ASSISTANT_MAX_SLOTS = int(os.getenv("ASSISTANT_MAX_SLOTS", "6"))
ASSISTANT_HISTORY_TURNS = int(os.getenv("ASSISTANT_HISTORY_TURNS", "4"))
