from pydantic import BaseModel, ConfigDict


class CredentialError(Exception):
    """Raise if token is not valid."""


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
    address_complement: str
    neighborhood: str
    city: str
    state: str
    country: str
    zip_code: str


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
