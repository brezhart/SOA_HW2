from datetime import date, datetime
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, Union

class UserBase(BaseModel):
    email: EmailStr
    first_name: str = Field(..., min_length=2, max_length=50)
    last_name: str = Field(..., min_length=2, max_length=50)
    birth_date: Optional[date]  = None
    phone: Optional[str] = Field(None, regex=r"^\+?[1-9]\d{1,14}$")  # E.164 format
    avatar_url: Optional[str] = None  # Дополнительное поле

class UserCreate(UserBase):
    login: str = Field(..., min_length=3, max_length=50, regex=r"^[a-zA-Z0-9_]+$")
    password: str = Field(..., min_length=8)

    @validator("password")
    def validate_password(cls, v):
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v

class UserUpdate(UserBase):
    email: Optional[EmailStr] = None
    first_name: Optional[str] = Field(None, min_length=2, max_length=50)
    last_name: Optional[str] = Field(None, min_length=2, max_length=50)
    birth_date: Optional[date] = None
    phone: Optional[str] = Field(None, regex=r"^\+?[1-9]\d{1,14}$")
    avatar_url: Optional[str] = None

class UserInDB(UserBase):
    id: int
    login: str
    created_at: datetime
    updated_at: datetime
    is_active: bool

    class Config:
        orm_mode = True

class UserResponse(UserInDB):
    pass  # Можно исключить sensitive данные при необходимости

class LoginRequest(BaseModel):
    login: str
    password: str

