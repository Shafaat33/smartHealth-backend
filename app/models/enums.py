import enum


class UserRole(str, enum.Enum):
    provider = "provider"
    patient = "patient"
    front_desk = "front_desk"


class Specialty(str, enum.Enum):
    family_medicine = "family_medicine"
    cardiology = "cardiology"
    dermatology = "dermatology"
    orthopedics = "orthopedics"
    gastroenterology = "gastroenterology"
    endocrinology = "endocrinology"
    pediatrics = "pediatrics"
    obgyn = "obgyn"
    mental_health = "mental_health"


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
    