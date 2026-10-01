class EmailAlreadyExists(Exception):
    def __init__(self, message: str = "Email already registered"):
        super().__init__(message)


class InvalidCredentials(Exception):
    def __init__(self, message: str = "Invalid email or password"):
        super().__init__(message)


class InactiveUser(Exception):
    def __init__(self, message: str = "Account is inactive"):
        super().__init__(message)


class PatientNotFound(Exception):
    def __init__(self, message: str = "Patient not found"):
        super().__init__(message)


class ProviderNotFound(Exception):
    def __init__(self, message: str = "Provider not found"):
        super().__init__(message)


class Forbidden(Exception):
    def __init__(self, message: str = "Forbidden"):
        super().__init__(message)


class AppointmentNotFound(Exception):
    def __init__(self, message: str = "Appointment not found"):
        super().__init__(message)


class InvalidAppointmentTransition(Exception):
    def __init__(self, current: str, new: str):
        super().__init__(f"Cannot change appointment status from {current} to {new}")


class SlotTaken(Exception):
    def __init__(self, message: str = "This provider already has an appointment at that time"):
        super().__init__(message)


class AppointmentTimeInPast(Exception):
    def __init__(self, message: str = "Appointment time must be in the future"):
        super().__init__(message)
