from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.constants import ANALYTICS_URL
from app.core.deps import require_role
from app.db.session import get_db
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.analytics import AnalyticsRead
from app.services.analytics import AnalyticsService

router = APIRouter(prefix=ANALYTICS_URL, tags=["analytics"])


@router.get("", response_model=AnalyticsRead)
def get_analytics(
    db: Session = Depends(get_db),
    _: User = Depends(require_role(UserRole.front_desk)),
):
    return AnalyticsService(db).snapshot()
