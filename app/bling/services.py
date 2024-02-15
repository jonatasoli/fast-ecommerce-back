from decimal import Decimal
from xml.etree import ElementTree as ET

import requests
from dynaconf import settings
from pydantic import BaseModel, field_validator

from app.infra import redis

cache = redis.RedisCache()


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


class ClientParser(BaseModel):
    nome: str
    tipo_pessoa: str
    cpf_cnpj: str | None = None
    ie_rg: str | None = None
    contribuinte: str | None = None
    endereco: str
    numero: str
    complemento: str | None = None
    bairro: str
    cep: str
    cidade: str
    uf: str
    pais: str | None = None
    fone: str | None = None
    email: str

    @classmethod
    @field_validator("nome")
    def validate_nome(cls, v):
        if len(v) > 80:
            raise ValueError('Nome não pode ter mais de 80 caracteres')
        return v

    @classmethod
    @field_validator("tipo_pessoa")
    def validate_tipo_pessoa(cls, v):
        if v not in ['F', 'J', 'E'] or len(v) > 1:
            raise ValueError('Tipo de pessoa inválido')
        return v

    @classmethod
    @field_validator("cpf_cnpj")
    def validate_cpf_cnpj(cls, v):
        if len(v) > 18:
            raise ValueError('CPF/CNPJ inválido')
        return v

    @classmethod
    @field_validator("ie_rg")
    def validade_ie_rg(cls, v):
        if len(v) > 18:
            raise ValueError('IE/RG inválido')
        return v

    @classmethod
    @field_validator("contribuinte")
    def validate_contribuinte(cls, v):
        if len(v) > 1:
            raise ValueError('Contribuinte inválido')
        return v

    @classmethod
    @field_validator("endereco")
    def validate_endereco(cls, v):
        if len(v) > 100:
            raise ValueError('Endereço inválido')
        return v

    @classmethod
    @field_validator("numero")
    def validate_numero(cls, v):
        if len(v) > 10:
            raise ValueError('Número inválido')
        return v

    @classmethod
    @field_validator("bairro")
    def validate_bairro(cls, v):
        if len(v) > 40:
            raise ValueError('Bairro inválido')
        return v

    @classmethod
    @field_validator("cep")
    def validate_cep(cls, v):
        if len(v) > 10:
            raise ValueError('CEP inválido')
        return v

    @classmethod
    @field_validator("cidade")
    def validate_cidade(cls, v):
        if len(v) > 30:
            raise ValueError('Cidade inválida')
        return v

    @classmethod
    @field_validator("uf")
    def validate_uf(cls, v):
        if len(v) > 2:
            raise ValueError('UF inválido')
        return v

    @classmethod
    @field_validator("fone")
    def validate_fone(cls, v):
        if len(v) > 40:
            raise ValueError('Telefone inválido')
        return v

    @classmethod
    @field_validator("email")
    def validate_email(cls, v):
        if len(v) > 60:
            raise ValueError('Email inválido')
        return v


class TransporteParser(BaseModel):
    transportadora: str | None = None
    cpf_cnpj: str | None = None
    ie_rg: str | None = None
    endereco: str | None = None
    cidade: str | None = None
    uf: str | None = None
    qtde_volumes: int | None = None
    peso_bruto: Decimal | None = None
    peso_liquido: Decimal | None = None

    @classmethod
    @field_validator('uf')
    def validate_uf(cls, v):
        if len(v) > 2:
            raise ValueError('UF inválido')
        return v

    @classmethod
    @field_validator('cidade')
    def validate_cidade(cls, v):
        if len(v) > 40:
            raise ValueError('Cidade inválida')
        return v

    @classmethod
    @field_validator('endereco')
    def validate_endereco(cls, v):
        if len(v) > 50:
            raise ValueError('Endereço inválido')
        return v

    @classmethod
    @field_validator('ie_rg')
    def validate_ie_rg(cls, v):
        if len(v) > 18:
            raise ValueError('IE/RG inválido')
        return v

    @classmethod
    @field_validator('cpf_cnpj')
    def validate_cpf_cnpj(cls, v):
        if len(v) > 18:
            raise ValueError('CPF/CNPJ inválido')
        return v

    @classmethod
    @field_validator('transportadora')
    def validate_transportadora(cls, v):
        if len(v) > 100:
            raise ValueError('Transportadora inválida')
        return v


class XMLParser(BaseModel):
    cliente: list[ClientParser]
    transporte: list[TransporteParser]


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
                "peso_liquido": 10.0
            }
        ]
    )
    return data


def generate_xml(data: XMLParser):
    root = ET.Element("pedido")
    for element in data:
        sub_element = ET.SubElement(root, element[0])
        for value in element:
            if isinstance(value, list):
                values = value[0].model_dump()
                for k, v in values.items():
                    if not v:
                        continue
                    ET.SubElement(sub_element, k).text = str(v)
    tree = ET.ElementTree(root)
    tree.write(
        'filename.xml', encoding="utf-8", xml_declaration=True, short_empty_elements=False
    )
    return


generate_xml(get_xml_data())