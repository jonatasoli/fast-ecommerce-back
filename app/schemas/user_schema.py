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
