from pydantic import BaseModel, AnyUrl

class PaymentConfig(BaseModel):
    provider: str
    field: str = "PAYMENT"
    description: str
    gateway_name: str
    gateway_url: AnyUrl
    gateway_key: str
    gateway_secret_key: str

class LogisticsConfig(BaseModel):
    provider: str
    field: str = "LOGISTIC"
    description: str
    name: str
    logistics_user: str
    logistics_pass: str
    logistics_api_secret: str
    logistics_postal_card: str
    zip_origin: str

class NotificationConfig(BaseModel):
    provider: str
    field: str = "NOTIFICATION"
    description: str
    type: str
    contact: str
    api_key: str
    secret_key: str

class CDNConfig(BaseModel):
    provider: str
    field: str = "CDN"
    description: str
    provider: str
    url: AnyUrl
    region: str
    bucket_name: str
    api_key: str
    secret_key: str

class CompanyConfig(BaseModel):
    provider: str
    field: str = "COMPANY"
    description: str
    name: str

class CRMConfig(BaseModel):
    provider: str
    field: str = "CRM"
    description: str
    access_key: str
    url: AnyUrl
    deal_stage_id: str
    deal_stage_name: str

class MainSettings(BaseModel):
    locale: str
    is_default: bool = False
    payment: PaymentConfig | None
    logistics: LogisticsConfig | None
    notification: NotificationConfig | None
    cdn: CDNConfig | None
    company: CompanyConfig | None
    crm: CRMConfig | None
