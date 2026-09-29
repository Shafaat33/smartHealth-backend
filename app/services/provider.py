from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import EmailAlreadyExists, ProviderNotFound
from app.core.security import hash_password
from app.models.enums import UserRole
from app.models.provider import Provider
from app.models.user import User
from app.repositories.provider import ProviderRepository
from app.repositories.user import UserRepository
from app.schemas.provider import ProviderCreate


class ProviderService:
    def __init__(self, db: Session):
        self.db = db
        self.users = UserRepository(db)
        self.providers = ProviderRepository(db)

    def create(self, payload: ProviderCreate) -> Provider:
        email = payload.email.strip().lower()

        if self.users.get_by_email(email) is not None:
            raise EmailAlreadyExists()

        user = User(
            name=payload.name.strip(),
            email=email,
            hashed_password=hash_password(payload.password),
            role=UserRole.provider,
        )
        self.users.add(user)

        try:
            self.db.flush()
            provider = Provider(user_id=user.id)
            self.providers.add(provider)
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            raise EmailAlreadyExists() from None

        self.db.refresh(provider)
        return provider

    def get_me(self, current_user: User) -> Provider:
        provider = self.providers.get_by_user_id(current_user.id)
        if provider is None:
            raise ProviderNotFound()
        return provider

    def get_by_id(self, provider_id: UUID) -> Provider:
        provider = self.providers.get_by_id(provider_id)
        if provider is None:
            raise ProviderNotFound()
        return provider

    def list(self) -> list[Provider]:
        return self.providers.list()
