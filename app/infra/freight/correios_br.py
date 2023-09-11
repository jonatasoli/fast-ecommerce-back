import httpx
from config import settings
from httpx import Auth, TimeoutException
import base64


base_url = settings.CORREIOSBR_API_URL


def get_token():
    url = base_url + '/v1/autentica'
    client = httpx.Client(timeout=settings.CLIENT_API_TIMEOUT)
<<<<<<< HEAD
    basic_auth = (
        f'{settings.CORREIOSBR_USER}:{settings.CORREIOSBR_API_SECRET}'.encode()
    )
    credenciais_base64 = base64.b64encode(basic_auth).decode('utf-8')
=======
    basic_auth = f'{settings.CORREIOSBR_USER}:{settings.CORREIOSBR_API_SECRET}'.encode('utf-8')
    credenciais_base64 = base64.b64encode(basic_auth).decode('utf-8')
    # basic_auth = (settings.CORREIOSBR_USER, settings.CORREIOSBR_PASSWORD)
>>>>>>> d09b06e (feat: integrate with correiosbr api)
    headers = {
        'accept': 'application/json',
        'Authorization': f'Basic {credenciais_base64}',
    }
    if not (response := client.post(url, headers=headers)):
<<<<<<< HEAD
        msg = 'Erro to connect with corrios api'
        raise TimeoutException(msg)
    return response.json()['token']
=======
        raise TimeoutException(f'Erro to connect with corrios api')
    return response.json()['token']



>>>>>>> d09b06e (feat: integrate with correiosbr api)
