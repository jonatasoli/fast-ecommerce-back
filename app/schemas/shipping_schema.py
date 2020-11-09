from pydantic import BaseModel

class Shipping(BaseModel):
    zip_code_target: str
    weigth: str
    length: str
    heigth: str
    width:  str
    diameter: str