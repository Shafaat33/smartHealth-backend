class EmailAlreadyExists(Exception):
    def __init__(self, message: str = "Email already registered"):
        super().__init__(message)


class InvalidCredentials(Exception):
    def __init__(self, message: str = "Invalid email or password"):
        super().__init__(message)


class InactiveUser(Exception):
    def __init__(self, message: str = "Account is inactive"):
        super().__init__(message)
