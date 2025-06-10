
import json
from pydantic import AnyUrl
from sqlalchemy import select
from app.infra.cryptography import decrypt, encrypt
from config import settings

from app.entities.settings import MainSettings
from app.infra.models import SettingsDB


class SettingsInputError(Exception):
    ...


async def get_settings(
    *,
    locale: str,
    field: str,
    transaction,
):
    """Repository to get a setting for field and locale."""
    query = select(SettingsDB).where(
        SettingsDB.locale.like(locale),
    ).where(
        SettingsDB.field.like(field),
    )
    field = await transaction.scalar(query)
    if not field:
        query = select(SettingsDB).where(
            SettingsDB.field.like(field),
        ).where(
            SettingsDB.is_default.is_(True),
        )
        field = await transaction.scalar(query)
    message = field.credentials
    field_decript = decrypt(message, settings.SECRET_KEY).decode()
    field.credentials = json.loads(field_decript)
    return field

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
    """Update or create a setting."""
    filled_fields = {
        field: value for field, value in setting.dict(
            exclude_unset=True,
        ).items() if field not in ['locale', 'is_default'] and value is not None
    }
    if not filled_fields:
        raise SettingsInputError

    _, field_value = next(iter(filled_fields.items()))
    field_value = serialize_data(field_value)
    setting_db = await get_settings(
        locale=locale, field=field_value.get('field'), transaction=transaction)
    key = settings.SECRET_KEY
    credentials = encrypt(json.dumps(field_value), key)
    if not setting_db:
        setting_db = SettingsDB(
            locale=locale,
            is_default=setting.is_default,
            provider=field_value.get("provider"),
            field=field_value.get('field'),
            value=json.dumps(field_value),
            credentials=credentials,
        )
        return transaction.add(setting)
    setting_db.field = field_value.get('field')
    setting_db.provider = field_value.get("provider")
    setting_db.value = json.dumps(field_value)
    setting_db.locale = locale

    transaction.add(setting_db)
    return setting_db

