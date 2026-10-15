from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import EmailAlreadyExists, InactiveUser, InvalidCredentials
from app.core.security import create_access_token, hash_password, verify_password
from app.models.enums import UserRole
from app.models.patient import Patient
from app.models.user import User
from app.repositories.patient import PatientRepository
from app.repositories.user import UserRepository
from app.schemas.user import Token, UserLogin, UserRegister


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.users = UserRepository(db)
        self.patients = PatientRepository(db)

    def register(self, payload: UserRegister) -> User:
        email = payload.email.strip().lower()

        if self.users.get_by_email(email) is not None:
            raise EmailAlreadyExists()

        user = User(
            name=payload.name.strip(),
            email=email,
            hashed_password=hash_password(payload.password),
            role=UserRole.patient,
        )
        self.users.add(user)

        try:
            self.db.flush()
            self.patients.add(Patient(user_id=user.id))
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            raise EmailAlreadyExists() from None

        self.db.refresh(user)
        return user

    def login(self, payload: UserLogin) -> Token:
        email = payload.email.strip().lower()
        user = self.users.get_by_email(email)

        if user is None or not verify_password(payload.password, user.hashed_password):
            raise InvalidCredentials()

        if not user.is_active:
            raise InactiveUser()

        return Token(
            access_token=create_access_token(user.id, user.role.value),
        )
