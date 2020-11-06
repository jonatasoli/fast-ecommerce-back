from pydantic import BaseModel, SecretStr
from typing import Optional


class Login(BaseModel):
    document: str
    password: SecretStr


class SignUp(BaseModel):
    name: str
    mail: str
    password: SecretStr
    document: str
    phone: str


class User(SignUp):
    ...


class Token(BaseModel):
    access_token: str
    token_type: str


class FakeUser(BaseModel):
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    disabled: Optional[bool] = None


class UserInDB(FakeUser):
    hashed_password: str


class LoginResponse(BaseModel):
    message: str


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
    zipcode:  str
    complement: str
    type_address: str
    category: str
