from pydantic import AnyUrl, BaseModel


class ConfigDefault(BaseModel):
    provider: str
    description: str


class PaymentConfig(ConfigDefault):
    field: str = 'PAYMENT'
    gateway_name: str
    gateway_url: AnyUrl
    gateway_key: str
    gateway_secret_key: str


class LogisticsConfig(ConfigDefault):
    field: str = 'LOGISTIC'
    name: str
    logistics_user: str
    logistics_pass: str
    logistics_api_secret: str
    logistics_postal_card: str
    zip_origin: str


class NotificationConfig(ConfigDefault):
    field: str = 'NOTIFICATION'
    type: str
    contact: str
    api_key: str
    secret_key: str


class CDNConfig(ConfigDefault):
    field: str = 'CDN'
    url: AnyUrl
    region: str
    bucket_name: str
    api_key: str
    secret_key: str


class CompanyConfig(ConfigDefault):
    field: str = 'COMPANY'
    name: str


class CRMConfig(ConfigDefault):
    field: str = 'CRM'
    access_key: str
    url: AnyUrl
    deal_stage_id: str
    deal_stage_name: str


class MailGateway(ConfigDefault):
    field: str = 'MAIL'
    key: str | None
    secret: str


class MainSettings(BaseModel):
    locale: str
    is_default: bool = False
    payment: PaymentConfig | None
    logistics: LogisticsConfig | None
    notification: NotificationConfig | None
    cdn: CDNConfig | None
    company: CompanyConfig | None
    crm: CRMConfig | None
    mail: MailGateway | None
