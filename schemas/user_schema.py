from typing import Optional

from pydantic import BaseModel, SecretStr


class SignUp(BaseModel):
    name: str
    mail: str
    password: SecretStr
    document: str
    phone: str


class UserSchema(BaseModel):
    name: str
    password: str
    document: str
    phone: str
    role_id: int
    email: Optional[str] = None
    full_name: Optional[str] = None
    disabled: Optional[bool] = None

    class Config:
        orm_mode = True


class Token(BaseModel):
    access_token: str
    token_type: str
    role: str


class UserInDB(UserSchema):
    password: str
    role_id: int


class SignUpResponse(BaseModel):
    name: str
    message: str


class AddressSchema(BaseModel):
    country: str
    state: str
    city: str
    neighborhood: str
    street: str
    street_number: str
    zipcode: str
    complement: str
    type_address: str
    category: str


class UserResponseResetPassword(BaseModel):
    document: str
    password: str
