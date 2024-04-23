from xml.etree import ElementTree as ET

import requests
from dynaconf import settings

from app.bling.entities import XMLParser, TipoEnum
from app.infra import redis

cache = redis.RedisCache()

from loguru import logger


def get_access_token_by_refresh_token() -> int:
    url_refresh_token = f'{settings.BLING_TOKEN_URL}'
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Authorization': f'Basic {settings.BLING_AUTHORIZATION_CODE}'
    }

    body = {
        'grant_type': 'refresh_token',
        'refresh_token': settings.BLING_REFRESH_TOKEN
    }
    req = requests.post(url_refresh_token, headers=headers, data=body)

    return req.status_code


def get_xml_data() -> XMLParser:
    data = XMLParser(
        cliente=[
            {
                "nome": "Teste",
                "tipo_pessoa": "F",
                "cpf_cnpj": "12345678901",
                "ie_rg": "12345678901",
                "contribuinte": "I",
                "endereco": "Rua Teste",
                "numero": "123",
                "complemento": "Casa",
                "bairro": "Bairro Teste",
                "cep": "12345678",
                "cidade": "Cidade Teste",
                "uf": "SP",
                "fone": "1234567890",
                "email": "a@a.com"
            }
        ],
        transporte=[
            {
                "transportadora": "Teste",
                "cpf_cnpj": "12345678901",
                "ie_rg": "12345678901",
                "endereco": "Rua Teste",
                "cidade": "Cidade Teste",
                "uf": "SP",
                "qtde_volumes": 1,
                "peso_bruto": 10.0,
                "peso_liquido": 10.0,
                "dados_etiqueta": {
                    "nome": "Endereço de entrega",
                    "endereco": "Rua Visconde de São Gabriel",
                    "numero": "392",
                    "complemento": "Sala 59",
                    "municipio": "Bento Gonçalves",
                    "uf": "RS",
                    "cep": "95.700-000",
                    "bairro": "Cidade Alta"
                },
            }
        ],
        itens=[
            {
                "descricao": "Teste 1",
                "un": "UN",
                "qtde": 1,
                "vlr_unit": 8.0,
                "tipo": TipoEnum.produto
            },
            {
                "descricao": "Dois testes",
                "un": "CX",
                "qtde": 2,
                "vlr_unit": 12.0,
                "tipo": TipoEnum.produto
            }, {
                "descricao": "Teste 1",
                "un": "UN",
                "qtde": 1,
                "vlr_unit": 8.0,
                "tipo": TipoEnum.produto
            }, {
                "descricao": "Teste 1",
                "un": "UN",
                "qtde": 1,
                "vlr_unit": 8.0,
                "tipo": TipoEnum.servico
            },
        ],

    )
    return data


SUB_LEVEL_ELEMENTS = {
    'itens': 'item',
}


def generate_xml(data: XMLParser):
    root = ET.Element("pedido")
    try:
        for element in data:
            sub_element = ET.SubElement(root, element[0])
            for value in element[1]:
                values = value.model_dump()
                sub_level = (
                    ET.SubElement(sub_element, SUB_LEVEL_ELEMENTS[element[0]])
                    if element[0] in SUB_LEVEL_ELEMENTS
                    else None
                )
                for k, v in values.items():
                    if not v:
                        continue
                    if k == 'dados_etiqueta':
                        sub_ = ET.SubElement(sub_element, k)
                        for key, values in v.items():
                            ET.SubElement(sub_, key).text = str(values)
                        continue
                    if sub_level is not None:
                        ET.SubElement(sub_level, k).text = str(v)
                        continue
                    ET.SubElement(sub_element, k).text = str(v)
        tree = ET.ElementTree(root)
        tree.write(
            'filename.xml', encoding="utf-8", xml_declaration=True, short_empty_elements=False
        )
    except Exception as e:
        logger.error(e)
    return


generate_xml(get_xml_data())
