import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Enum as SqlEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin
from .enums import UserRole

if TYPE_CHECKING:
    from .provider import Provider
    from .patient import Patient


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str]
    role: Mapped[UserRole] = mapped_column(SqlEnum(UserRole, name="user_role"))
    email: Mapped[str] = mapped_column(unique=True, index=True)
    hashed_password: Mapped[str]
    is_active: Mapped[bool] = mapped_column(default=True, server_default="true")

    provider: Mapped["Provider | None"] = relationship(back_populates="user", uselist=False)
    patient: Mapped["Patient | None"] = relationship(back_populates="user", uselist=False)
