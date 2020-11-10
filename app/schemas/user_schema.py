from pydantic import BaseModel, SecretStr
from typing import Optional


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
    email: Optional[str] = None
    full_name: Optional[str] = None
    disabled: Optional[bool] = None

    class Config:
        orm_mode = True


class Token(BaseModel):
    access_token: str
    token_type: str


class UserInDB(UserSchema):
    password: str


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
