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
    field: str = 'LOGISTICS'
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
    key: str | None = None
    secret: str


class BucketConfig(ConfigDefault):
    field: str = 'BUCKET'
    provider: str
    secret: str
    key: str


class MainSettings(BaseModel):
    locale: str
    is_default: bool = False
    payment: PaymentConfig | None = None
    logistics: LogisticsConfig | None = None
    notification: NotificationConfig | None = None
    cdn: CDNConfig | None = None
    company: CompanyConfig | None = None
    crm: CRMConfig | None = None
    mail: MailGateway | None = None
    bucket: BucketConfig | None = None


class SettingsResponse(BaseModel):
    """Settings response with obfuscated sensitive fields."""
    settings_id: int
    locale: str
    provider: str
    field: str
    value: dict
    description: str | None
    is_active: bool
    is_default: bool


class SettingsCreate(BaseModel):
    """Settings create request."""
    locale: str
    provider: str
    field: str
    value: dict
    description: str | None = None
    is_active: bool = True
    is_default: bool = False


class SettingsUpdate(BaseModel):
    """Settings update request."""
    locale: str | None = None
    provider: str | None = None
    field: str | None = None
    value: dict | None = None
    description: str | None = None
    is_active: bool | None = None
    is_default: bool | None = None


class SettingsListResponse(BaseModel):
    """List of settings."""
    settings: list[SettingsResponse]
    total: int
