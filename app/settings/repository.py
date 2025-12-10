import json
from cryptography.fernet import InvalidToken
from loguru import logger
from pydantic import AnyUrl
from sqlalchemy import select, update, func
from app.infra.crypto_tools import decrypt, encrypt
from config import settings

from app.entities.settings import MainSettings, SettingsCreate, SettingsUpdate
from app.infra.models import SettingsDB


class SettingsInputError(Exception): ...


SENSITIVE_FIELDS = {
    'PAYMENT': ['gateway_key', 'gateway_secret_key'],
    'LOGISTICS': ['logistics_user', 'logistics_pass', 'logistics_api_secret'],
    'NOTIFICATION': ['api_key', 'secret_key'],
    'CDN': ['api_key', 'secret_key'],
    'CRM': ['access_key'],
    'MAIL': ['key', 'secret'],
    'BUCKET': ['secret', 'key'],
}


def obfuscate_value(value: str, show_chars: int = 4) -> str:
    """Ofuscar valor sensível mostrando apenas alguns caracteres."""
    if not value or len(value) <= show_chars:
        return '*' * len(value) if value else ''
    return value[:show_chars] + '*' * (len(value) - show_chars)


def obfuscate_settings_value(field_type: str, value_dict: dict) -> dict:
    """Ofuscar campos sensíveis no valor do setting."""
    if field_type not in SENSITIVE_FIELDS:
        return value_dict

    obfuscated = value_dict.copy()
    sensitive_keys = SENSITIVE_FIELDS[field_type]

    for key in sensitive_keys:
        if obfuscated.get(key):
            obfuscated[key] = obfuscate_value(str(obfuscated[key]))

    return obfuscated


def _get_settings_from_env(field: str, locale: str = 'pt-br') -> SettingsDB | None:
    """Get settings from environment variables as fallback.

    Returns a SettingsDB-like object with values from env vars.
    """

    env_mapping = {
        'CDN': {
            'provider': 'S3',
            'url': getattr(settings, 'ENDPOINT_UPLOAD_CLIENT', ''),
            'region': getattr(settings, 'ENDPOINT_UPLOAD_REGION', ''),
            'bucket_name': getattr(settings, 'BUCKET_NAME', ''),
            'api_key': getattr(settings, 'AWS_ACCESS_KEY_ID', ''),
            'secret_key': getattr(settings, 'AWS_SECRET_ACCESS_KEY', ''),
        },
        'PAYMENT': {
            'provider': getattr(settings, 'PAYMENT_GATEWAY', 'STRIPE'),
            'gateway_name': getattr(settings, 'PAYMENT_GATEWAY', 'STRIPE'),
            'gateway_url': getattr(settings, 'MERCADO_PAGO_URL', ''),
            'gateway_key': getattr(settings, 'MERCADO_PAGO_PUBLIC_KEY', ''),
            'gateway_secret_key': getattr(settings, 'MERCADO_PAGO_ACCESS_TOKEN', ''),
        },
        'LOGISTICS': {
            'provider': 'Correios',
            'name': 'Correios',
            'logistics_user': getattr(settings, 'CORREIOSBR_USER', ''),
            'logistics_pass': getattr(settings, 'CORREIOSBR_PASS', ''),
            'logistics_api_secret': getattr(settings, 'CORREIOSBR_API_SECRET', ''),
            'logistics_postal_card': getattr(settings, 'CORREIOSBR_POSTAL_CART', ''),
            'zip_origin': getattr(settings, 'CORREIOSBR_CEP_ORIGIN', ''),
        },
        'NOTIFICATION': {
            'provider': 'Sendgrid',
            'type': 'Email',
            'contact': getattr(settings, 'EMAIL_FROM', ''),
            'api_key': getattr(settings, 'SENDGRID_API_KEY', ''),
            'secret_key': getattr(settings, 'SENDGRID_API_KEY', ''),
        },
        'COMPANY': {
            'provider': 'COMPANY',
            'name': getattr(settings, 'COMPANY', ''),
        },
        'MAIL': {
            'provider': 'resend',
            'key': getattr(settings, 'RESEND_API_KEY', ''),
            'secret': getattr(settings, 'RESEND_API_KEY', ''),
        },
        'BUCKET': {
            'provider': getattr(settings, 'FILE_UPLOAD_CLIENT', 'WASABI'),
            'secret': getattr(settings, 'AWS_SECRET_ACCESS_KEY', ''),
            'key': getattr(settings, 'AWS_ACCESS_KEY_ID', ''),
        },
    }

    if field not in env_mapping:
        return None

    env_values = env_mapping[field]

    has_values = any(
        v for k, v in env_values.items()
        if k not in ('provider', 'description') and v
    )

    if not has_values:
        return None

    class EnvSettingsDB:
        def __init__(self):
            self.settings_id = 0
            self.locale = locale
            self.provider = env_values.get('provider', '')
            self.field = field
            self.value = env_values
            self.credentials = None  # Não criptografar valores de env
            self.description = f'{field} settings from environment variables'
            self.is_active = True
            self.is_default = True

    setting_db = EnvSettingsDB()

    logger.info(f"Using environment variables for {field} (no DB setting found)")
    return setting_db


async def get_settings(  # noqa: C901
    *,
    locale: str,
    field: str,
    transaction,
):
    """Repository to get a setting for field and locale.

    Rules:
    1. First try to get setting with exact locale and field (prioritize default)
    2. If not found, try to get default setting for that field
    3. If still not found, get first active setting for that field
    4. If still not found, try to get from environment variables
    """
    query = (
        select(SettingsDB)
        .where(
            SettingsDB.locale == locale,
        )
        .where(
            SettingsDB.field == field,
        )
        .where(
            SettingsDB.is_active.is_(True),
        )
        .order_by(SettingsDB.is_default.desc())  # Default primeiro
        .limit(1)
    )
    setting = await transaction.scalar(query)

    if setting:
        if setting.credentials:
            try:
                message = setting.credentials.encode('utf-8')
                field_decript = decrypt(
                    message,
                    settings.CAPI_SECRET.encode(),
                ).decode()
                setting.value = json.loads(field_decript)
            except (ValueError, InvalidToken, json.JSONDecodeError) as e:
                logger.warning(f"Error decrypting setting {field}: {e}")
        return setting

    query = (
        select(SettingsDB)
        .where(
            SettingsDB.field == field,
        )
        .where(
            SettingsDB.is_default.is_(True),
        )
        .where(
            SettingsDB.is_active.is_(True),
        )
        .limit(1)
    )
    setting = await transaction.scalar(query)

    if setting:
        if setting.credentials:
            try:
                message = setting.credentials.encode('utf-8')
                field_decript = decrypt(
                    message,
                    settings.CAPI_SECRET.encode(),
                ).decode()
                setting.value = json.loads(field_decript)
            except (ValueError, InvalidToken, json.JSONDecodeError) as e:
                logger.warning(f"Error decrypting setting {field}: {e}")
        return setting

    query = (
        select(SettingsDB)
        .where(
            SettingsDB.field == field,
        )
        .where(
            SettingsDB.is_active.is_(True),
        )
        .order_by(SettingsDB.settings_id)
        .limit(1)
    )
    setting = await transaction.scalar(query)

    if setting:
        if setting.credentials:
            try:
                message = setting.credentials.encode('utf-8')
                field_decript = decrypt(
                    message,
                    settings.CAPI_SECRET.encode(),
                ).decode()
                setting.value = json.loads(field_decript)
            except (ValueError, InvalidToken, json.JSONDecodeError) as e:
                logger.warning(f"Error decrypting setting {field}: {e}")
        return setting

    env_setting = _get_settings_from_env(field, locale)
    if env_setting:
        return env_setting

    msg = (
        f"No setting found for field '{field}' and locale '{locale}', "
        "and no env vars available"
    )
    logger.warning(msg)
    return None


async def list_settings(  # noqa: PLR0913
    *,
    field: str | None = None,
    locale: str | None = None,
    is_active: bool | None = None,
    transaction,
    offset: int = 0,
    limit: int = 100,
) -> tuple[list[SettingsDB], int]:
    """List settings with filters."""
    query = select(SettingsDB)
    count_query = select(func.count(SettingsDB.settings_id))

    conditions = []
    if field:
        conditions.append(SettingsDB.field == field)
    if locale:
        conditions.append(SettingsDB.locale == locale)
    if is_active is not None:
        conditions.append(SettingsDB.is_active.is_(is_active))

    if conditions:
        for condition in conditions:
            query = query.where(condition)
            count_query = count_query.where(condition)

    query = query.order_by(SettingsDB.field, SettingsDB.locale, SettingsDB.settings_id)
    query = query.offset(offset).limit(limit)

    settings_list = (await transaction.scalars(query)).unique().all()
    total = await transaction.scalar(count_query)

    for setting in settings_list:
        if setting.credentials:
            try:
                message = setting.credentials.encode('utf-8')
                field_decript = decrypt(
                    message,
                    settings.CAPI_SECRET.encode(),
                ).decode()
                setting.value = json.loads(field_decript)
            except (ValueError, InvalidToken, json.JSONDecodeError) as e:
                logger.warning(f"Error decrypting setting {setting.settings_id}: {e}")

    return list(settings_list), total


async def get_setting_by_id(
    *,
    settings_id: int,
    transaction,
) -> SettingsDB | None:
    """Get setting by ID."""
    query = select(SettingsDB).where(SettingsDB.settings_id == settings_id)
    setting = await transaction.scalar(query)

    if setting and setting.credentials:
        try:
            message = setting.credentials.encode('utf-8')
            field_decript = decrypt(
                message,
                settings.CAPI_SECRET.encode(),
            ).decode()
            setting.value = json.loads(field_decript)
        except (ValueError, InvalidToken, json.JSONDecodeError) as e:
            logger.warning(f"Error decrypting setting {settings_id}: {e}")

    return setting


async def _unset_other_defaults(
    *,
    field: str,
    locale: str,
    transaction,
    exclude_id: int | None = None,
) -> None:
    """Unset is_default for other settings with same field and locale."""
    query = (
        update(SettingsDB)
        .where(SettingsDB.field == field)
        .where(SettingsDB.locale == locale)
        .where(SettingsDB.is_default.is_(True))
        .values(is_default=False)
    )

    if exclude_id:
        query = query.where(SettingsDB.settings_id != exclude_id)

    await transaction.execute(query)


async def create_setting(
    *,
    setting_data: SettingsCreate,
    transaction,
) -> SettingsDB:
    """Create a new setting.

    Rules:
    - If is_default=True, unset other defaults for same field+locale
    - Encrypt credentials before saving
    """
    key = settings.CAPI_SECRET

    if setting_data.is_default:
        await _unset_other_defaults(
            field=setting_data.field,
            locale=setting_data.locale,
            transaction=transaction,
        )

    credentials = encrypt(
        json.dumps(setting_data.value).encode(),
        key.encode(),
    )

    setting_db = SettingsDB(
        locale=setting_data.locale,
        provider=setting_data.provider,
        field=setting_data.field,
        value=json.dumps(setting_data.value),
        credentials=credentials.decode('utf-8'),
        description=setting_data.description,
        is_active=setting_data.is_active,
        is_default=setting_data.is_default,
    )

    transaction.add(setting_db)
    await transaction.flush()
    await transaction.refresh(setting_db)

    return setting_db


async def update_setting(
    *,
    settings_id: int,
    setting_data: SettingsUpdate,
    transaction,
) -> SettingsDB:
    """Update a setting.

    Rules:
    - If is_default=True, unset other defaults for same field+locale
    - Encrypt credentials if value is updated
    """
    setting_db = await get_setting_by_id(
        settings_id=settings_id,
        transaction=transaction,
    )

    if not setting_db:
        msg = f"Setting {settings_id} not found"
        raise SettingsInputError(msg)

    key = settings.CAPI_SECRET

    if setting_data.locale is not None:
        setting_db.locale = setting_data.locale
    if setting_data.provider is not None:
        setting_db.provider = setting_data.provider
    if setting_data.field is not None:
        setting_db.field = setting_data.field
    if setting_data.description is not None:
        setting_db.description = setting_data.description
    if setting_data.is_active is not None:
        setting_db.is_active = setting_data.is_active

    if setting_data.is_default is True and not setting_db.is_default:
        await _unset_other_defaults(
            field=setting_db.field,
            locale=setting_db.locale,
            transaction=transaction,
            exclude_id=settings_id,
        )
        setting_db.is_default = True
    elif setting_data.is_default is False:
        setting_db.is_default = False

    if setting_data.value is not None:
        setting_db.value = json.dumps(setting_data.value)
        credentials = encrypt(
            json.dumps(setting_data.value).encode(),
            key.encode(),
        )
        setting_db.credentials = credentials.decode('utf-8')

    transaction.add(setting_db)
    await transaction.flush()
    await transaction.refresh(setting_db)

    return setting_db


async def delete_setting(
    *,
    settings_id: int,
    transaction,
) -> bool:
    """Delete a setting."""
    setting_db = await get_setting_by_id(
        settings_id=settings_id,
        transaction=transaction,
    )

    if not setting_db:
        return False

    await transaction.delete(setting_db)
    return True


def serialize_data(data: dict) -> dict:
    """Convert fields like 'Url' to strings for JSON serialization."""
    for key, value in data.items():
        if isinstance(value, AnyUrl):
            data[key] = str(value)
        elif isinstance(value, dict):
            data[key] = serialize_data(value)
    return data


async def update_or_create_setting(
    *,
    setting: MainSettings,
    locale: str,
    transaction,
):
    """Update or create a setting (legacy method for backward compatibility)."""
    filled_fields = {
        field: value
        for field, value in setting.dict(
            exclude_unset=True,
        ).items()
        if field not in ['locale', 'is_default'] and value is not None
    }
    if not filled_fields:
        raise SettingsInputError

    _, field_value = next(iter(filled_fields.items()))
    field_value = serialize_data(field_value)
    setting_db = await get_settings(
        locale=locale, field=field_value.get('field'), transaction=transaction,
    )
    key = settings.CAPI_SECRET
    logger.debug(field_value)
    credentials = encrypt(json.dumps(field_value).encode(), key.encode())
    logger.debug(f'CREDENTIAL - {credentials}')

    if setting.is_default:
        await _unset_other_defaults(
            field=field_value.get('field'),
            locale=locale,
            transaction=transaction,
        )

    if not setting_db:
        setting_db = SettingsDB(
            locale=locale,
            is_default=setting.is_default,
            provider=field_value.get('provider'),
            field=field_value.get('field'),
            value=json.dumps(field_value),
            credentials=credentials.decode('utf-8'),
        )
        transaction.add(setting_db)
        return setting_db

    setting_db.field = field_value.get('field')
    setting_db.provider = field_value.get('provider')
    setting_db.value = json.dumps(field_value)
    setting_db.locale = locale
    setting_db.credentials = credentials.decode('utf-8')
    setting_db.is_default = setting.is_default

    transaction.add(setting_db)
    logger.debug(
        f'DECRIPT DB {decrypt(setting_db.credentials, key.encode())}',
    )
    return setting_db
