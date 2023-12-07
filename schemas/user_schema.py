from pydantic import ConfigDict, BaseModel, SecretStr


class SignUp(BaseModel):
    name: str
    username: str
    mail: str
    password: SecretStr
    document: str
    phone: str


class UserSchema(BaseModel):
    id: int
    name: str
    password: str
    document: str
    phone: str
    role_id: int
    email: str | None = None
    full_name: str | None = None
    disabled: bool | None = None
    model_config = ConfigDict(from_attributes=True)


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
