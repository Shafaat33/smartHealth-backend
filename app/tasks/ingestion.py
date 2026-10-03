import json
import logging
from dataclasses import asdict

from app.celery_app import celery_app
from app.db.base import SessionLocal
from app.services.ingestion import IngestionService

logger = logging.getLogger(__name__)


@celery_app.task(name="ingest_knowledge")
def ingest_knowledge() -> dict:
    db = SessionLocal()
    try:
        return asdict(IngestionService(db).ingest_directory())
    finally:
        db.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print(json.dumps(ingest_knowledge.run(), indent=2))
