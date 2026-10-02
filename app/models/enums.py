import enum


class UserRole(str, enum.Enum):
    provider = "provider"
    patient = "patient"
    front_desk = "front_desk"


class AppointmentStatus(str, enum.Enum):
    pending = "pending"
    confirmed = "confirmed"
    complete = "complete"
    canceled = "canceled"


class AppointmentEventType(str, enum.Enum):
    booked = "appointment.booked"
    confirmed = "appointment.confirmed"
    rescheduled = "appointment.rescheduled"
    canceled = "appointment.canceled"
    completed = "appointment.completed"
    