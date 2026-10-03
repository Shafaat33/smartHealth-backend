from fastapi import APIRouter, Depends, HTTPException, status

from app.constants import KNOWLEDGE_URL
from app.core.deps import require_role
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.knowledge import IngestionQueued
from app.tasks.ingestion import ingest_knowledge

router = APIRouter(prefix=KNOWLEDGE_URL, tags=["knowledge"])


@router.post("/ingest", response_model=IngestionQueued, status_code=status.HTTP_202_ACCEPTED)
def queue_ingestion(_: User = Depends(require_role(UserRole.front_desk))):
    try:
        result = ingest_knowledge.delay()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Task queue unavailable",
        ) from exc
    return IngestionQueued(task_id=result.id)
