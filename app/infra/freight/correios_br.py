from datetime import date, datetime
from decimal import Decimal
from fastapi.encoders import jsonable_encoder
import httpx
from pydantic import BaseModel
from config import settings
from httpx import Auth, TimeoutException
import base64
from app.infra import redis
from loguru import logger


base_url = settings.CORREIOSBR_API_URL


SEDEX_AG = '03220'
PAC_AG = '03298'
PACKAGE_TYPE = '2'
MAX_WEIGHT = 30
MAX_LENGTH = 105
MAX_WIDTH = 105
MAX_HEIGHT = 105
MAX_DIAMETER = 91
MIN_LENGTH = 16
MIN_WIDTH = 11
MIN_HEIGHT = 2


class DeliveryParams(BaseModel):
    coProduto: str
    nuRequisicao: str = '1'
    cepOrigem: str
    cepDestino: str
    dtEvento: str = date.today().strftime('%d-%m-%Y')
    dataPostagem: date = date.today()


class DeliveryTime(BaseModel):
    idLote: str
    parametrosPrazo: list[DeliveryParams]


class DeliveryPriceParams(BaseModel):
    cepOrigem: str
    psObjeto: str
    tpObjeto: str
    comprimento: str
    largura: str
    altura: str
    cepDestino: str


class DeliveryParamsResponse(BaseModel):
    delivery_time: int
    max_date: datetime


class DeliveryPriceResponse(BaseModel):
    price: Decimal


def get_client(timeout: int = settings.CLIENT_API_TIMEOUT):
    return httpx.Client(timeout=timeout)


def generate_bacth_id(redis_client: redis.AbstractCache = redis.RedisCache()):
    """Generate batch id."""
    redis = redis_client.client()
    if not (batch_id := redis.get('correiosbr_batch_id')):
        batch_id = 1
    else:
        batch_id = int(batch_id) + 1
        redis.set('correiosbr_batch_id', batch_id)
    return str(batch_id)


def get_token(redis_client: redis.AbstractCache = redis.RedisCache()):
    """Get correios token if exists or create a new one."""
    _redis = redis_client.client()

    if not (token := _redis.get('correiosbr_token')):
        url = base_url + '/token/v1/autentica/cartaopostagem'
        data = jsonable_encoder(
            {'numero': str(settings.CORREIOSBR_POSTAL_CART)},
        )
        basic_auth = f'{settings.CORREIOSBR_USER}:{settings.CORREIOSBR_API_SECRET}'.encode()
        credenciais_base64 = base64.b64encode(basic_auth).decode('utf-8')
        headers = {
            'accept': 'application/json',
            'Content-Type': 'application/json',
            'Authorization': f'Basic {credenciais_base64}',
        }
        client = get_client()
        if not (response := client.post(url, json=data, headers=headers)):
            msg = 'Erro to connect with corrios api'
            raise TimeoutException(msg)
        token = response.json()['token']
        _redis.set('correiosbr_token', token, ex=72000)

    if isinstance(token, bytes):
        token = token.decode('utf-8')
    return token


def calculate_delivery_time(
    zip_code_destiny: str,
    product_code: str = PAC_AG,
) -> DeliveryParamsResponse:
    """Calculate delivery time."""
    zip_code_origin = str(settings.CORREIOSBR_CEP_ORIGIN)
    url = base_url + '/prazo/v1/nacional'
    delivery_params = DeliveryParams(
        coProduto=product_code,
        cepOrigem=zip_code_origin,
        cepDestino=zip_code_destiny,
    )
    delivery_time = DeliveryTime(
        idLote=generate_bacth_id(),
        parametrosPrazo=[delivery_params],
    )
    client = get_client()
    token = get_token()
    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}',
    }
    data = jsonable_encoder(delivery_time)
    if not (response := client.post(url, json=data, headers=headers)):
        msg = 'Erro to connect with corrios api'
        raise TimeoutException(msg)
    _response = response.json()
    logger.info(_response)
    if not (delivery_time_response := _response[0]['prazoEntrega']):
        msg = 'Error to calculate delivery time'
        raise Exception(msg)
    max_date = datetime.strptime(
        _response[0]['dataMaxima'],
        '%Y-%m-%dT%H:%M:%S',
    )
    return DeliveryParamsResponse(
        delivery_time=delivery_time_response,
        max_date=max_date,
    )


def calculate_delivery_price(
    product_code: str,
    *,
    package: DeliveryPriceParams,
) -> DeliveryPriceResponse:
    """Calculate delivery price with correios api."""
    client = get_client()
    token = get_token()
    url = base_url + f'/preco/v1/nacional/{product_code}'

    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}',
    }
    params = package.model_dump()

    if not (response := client.get(url, params=params, headers=headers)):
        msg = 'Erro to connect with corrios api'
        raise TimeoutException(msg)
    _response = response.json()
    if not (price := _response['pcFinal']):
        msg = 'Error to calculate delivery price'
        raise Exception(msg)
    _price = Decimal(price.replace(',', '.'))
    return DeliveryPriceResponse(price=_price)
