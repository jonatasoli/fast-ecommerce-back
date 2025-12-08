import enum

from pydantic import BaseModel, ConfigDict, SecretStr

from app.infra.constants import Direction, UserOrderBy


class CredentialError(Exception):
    """Raise if token is not valid."""


class UserDuplicateError(Exception):
    """Raise if user already signup in system."""


class UserNotFoundError(Exception):
    """Raise if user not found in database."""


class PasswordEmptyError(Exception):
    """Raise if password is empty."""


class UserNotAdminError(Exception):
    """Raise if user not admin."""


class UserData(BaseModel):
    user_id: int
    name: str
    email: str
    document: str
    phone: str
    model_config = ConfigDict(from_attributes=True)


class UserAddress(BaseModel):
    user_id: int | None
    address: str
    address_number: str
    address_complement: str | None
    neighborhood: str
    city: str
    state: str
    country: str
    zip_code: str


class UserAddressInDB(BaseModel):
    user_id: int | None
    street: str
    street_number: str
    address_complement: str
    neighborhood: str
    city: str
    state: str
    country: str
    zipcode: str
    model_config = ConfigDict(from_attributes=True)


class UserDBGet(BaseModel):
    user_id: int
    name: str
    email: str | None = None
    role_id: int
    document: str
    phone: str
    customer_id: str | None = None

    model_config = ConfigDict(from_attributes=True)


class UserCouponResponse(BaseModel):
    urls: list[str]


class SignUp(BaseModel):
    name: str
    username: str
    mail: str
    password: SecretStr
    document: str
    phone: str
    terms: bool = False


class Roles(enum.Enum):
    ADMIN = 1
    USER = 2
    PARTNER = 3


class DocumentType(enum.Enum):
    CPF = 'CPF'


class SignUpResponse(BaseModel):
    name: str
    message: str


class UserResponseResetPassword(BaseModel):
    document: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str
    role: str


class UserSchema(BaseModel):
    user_id: int
    name: str
    password: str
    document: str
    phone: str
    role_id: int
    email: str | None = None
    full_name: str | None = None
    disabled: bool | None = None
    addresses: list[UserAddressInDB] | None = None
    model_config = ConfigDict(from_attributes=True)


class UserInDB(UserSchema):
    password: str
    role_id: int


class UserUpdate(BaseModel):
    name: str | None = None
    document: str | None = None
    phone: str | None = None
    role_id: int | None = None
    email: str | None = None


class UsersDBResponse(BaseModel):
    users: list[UserInDB]
    page: int
    limit: int
    total_pages: int
    total_records: int


class UserFilters(BaseModel):
    search_name: str | None = None
    search_document: str | None = None
    order_by: UserOrderBy = UserOrderBy.user_id
    direction: Direction = Direction.asc
    limit: int = 10
    page: int = 1
