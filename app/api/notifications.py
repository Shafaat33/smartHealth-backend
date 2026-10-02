from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.constants import NOTIFICATION_URL
from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.notification import NotificationRead
from app.services.notification import NotificationService

router = APIRouter(prefix=NOTIFICATION_URL, tags=["notifications"])


@router.get("", response_model=list[NotificationRead])
def list_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return NotificationService(db).list_for_user(current_user)
