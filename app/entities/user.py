from pydantic import BaseModel


class UserData(BaseModel):
    name: str
    mail: str
    document: str
    phone: str


class UserAddress(BaseModel):
    user_id: int
    address: str
    address_number: str
    address_complement: str
    neighborhood: str
    city: str
    state: str
    country: str
    zip_code: str
