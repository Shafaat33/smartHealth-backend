import enum


class UserRole(str, enum.Enum):
    provider = "provider"
    patient = "patient"
    front_desk = "front_desk"


class AppointmentStatus(str, enum.Enum):
    pending = "pending"
    complete = "complete"
    canceled = "canceled"
    