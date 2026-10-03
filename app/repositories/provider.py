from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.enums import Specialty
from app.models.provider import Provider


class ProviderRepository:
    def __init__(self, db: Session):
        self.db = db

    def add(self, provider: Provider) -> Provider:
        self.db.add(provider)
        return provider

    def get_by_id(self, provider_id: UUID) -> Provider | None:
        return self.db.scalar(
            select(Provider)
            .options(joinedload(Provider.user))
            .where(Provider.id == provider_id)
        )

    def get_by_user_id(self, user_id: UUID) -> Provider | None:
        return self.db.scalar(
            select(Provider)
            .options(joinedload(Provider.user))
            .where(Provider.user_id == user_id)
        )

    def list(self, specialty: Specialty | None = None) -> list[Provider]:
        query = select(Provider).options(joinedload(Provider.user))
        if specialty is not None:
            query = query.where(Provider.specialty == specialty)
        return list(self.db.scalars(query.order_by(Provider.created_at)).all())
