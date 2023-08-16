from pydantic import BaseModel, ConfigDict


class UserData(BaseModel):
    name: str
    email: str
    document: str
    phone: str
    model_config = ConfigDict(from_attributes=True)


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
