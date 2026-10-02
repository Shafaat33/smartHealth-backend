import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin

if TYPE_CHECKING:
    from .user import User
    from .appointment import Appointment


class Provider(TimestampMixin, Base):
    __tablename__ = "providers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True)

    user: Mapped["User"] = relationship(back_populates="provider")
    appointments: Mapped[list["Appointment"]] = relationship(back_populates="provider")

    @property
    def name(self) -> str:
        return self.user.name if self.user is not None else ""
