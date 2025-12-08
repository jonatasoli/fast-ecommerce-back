import httpx
import requests
from loguru import logger
from app.entities.user import UserData
from app.infra.redis import RedisCache
from app.infra.settings import repository
from app.infra.database import get_async_session

CRM_FIELD = 'CRM'
DEFAULT_SUCESS_CODE = 200


class NotSendToCRMError(Exception): ...


async def send_abandonated_cart_to_crm(
    user_data: UserData, *, get_settings=repository.get_settings, db=get_async_session(),
):
    """Send user to CRM RD Station."""
    async with db.begin() as session:
        crm_settings = await get_settings(CRM_FIELD, transaction=session)

    _url = crm_settings.value.get('url')
    _access_key = crm_settings.value.get('access_key')
    _deal_stage_id = crm_settings.value.get('deal_stage_id')
    _deal_name = crm_settings.value.get('deal_stage_name')
    _payload = {
        'deal': {
            'deal_stage_id': f'{_deal_stage_id}',
            'name': f'{_deal_name}',
        },
        'contacts': [
            {
                'emails': [{'email': f'{user_data.email}'}],
                'name': f'{user_data.name}',
                'phones': [
                    {
                        'phone': f'{user_data.phone}',
                        'type': 'cellphone',
                    },
                ],
            },
        ],
    }
    headers = {
        'accept': 'application/json',
        'content-type': 'application/json',
    }

    lead = requests.post(
        f'{_url}/deals?token={_access_key}', json=_payload, headers=headers, timeout=500,
    )
    if lead.status_code != DEFAULT_SUCESS_CODE:
        raise NotSendToCRMError
    logger.info('Client enviado com sucesso')
    logger.info(lead.content)
