from pydantic import BaseModel, SecretStr


class Login(BaseModel):
    document: str
    password: SecretStr


class SignUp(BaseModel):
    name: str
    mail: str
    password: SecretStr
    document: str
    phone: str


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
