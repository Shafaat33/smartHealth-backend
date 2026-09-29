from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.provider import Provider


class ProviderRepository:
    def __init__(self, db: Session):
        self.db = db

    def add(self, provider: Provider) -> Provider:
        self.db.add(provider)
        return provider

    def get_by_id(self, provider_id: UUID) -> Provider | None:
        return self.db.get(Provider, provider_id)

    def get_by_user_id(self, user_id: UUID) -> Provider | None:
        return self.db.scalar(select(Provider).where(Provider.user_id == user_id))

    def list(self) -> list[Provider]:
        return list(self.db.scalars(select(Provider).order_by(Provider.created_at)).all())
