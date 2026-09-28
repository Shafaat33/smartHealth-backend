import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import UserRole


# ---------- Base / shared fields ----------

class UserBase(BaseModel):
    name: str
    email: str
    role: UserRole


# ---------- Create (input, e.g. POST /users) ----------

class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=72)


class UserRegister(BaseModel):
    name: str
    email: str
    password: str = Field(min_length=8, max_length=72)


# ---------- Login (input, e.g. POST /auth/login) ----------

class UserLogin(BaseModel):
    email: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ---------- Update (input, e.g. PATCH /users/{id}) ----------

class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None


# ---------- Read (output, e.g. GET /users/{id}) ----------

class UserRead(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    is_active: bool
    created_at: datetime
