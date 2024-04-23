from decimal import Decimal

from pydantic import BaseModel, field_validator


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


class DadosEtiquetaParser(BaseModel):
    nome: str | None = None
    endereco: str | None = None
    numero: str | None = None
    complemento: str | None = None
    municipio: str | None = None
    uf: str | None = None
    cep: str | None = None
    bairro: str | None = None

    @classmethod
    @field_validator('nome')
    def validate_nome(cls, v):
        if len(v) > 120:
            raise ValueError('Nome tem que ter menos que 120 caracteres')
        return v

    @classmethod
    @field_validator('endereco')
    def validate_endereco(cls, v):
        if len(v) > 50:
            raise ValueError('Endereço tem que ter menos que 50 caracteres')
        return v

    @classmethod
    @field_validator('numero')
    def validate_numero(cls, v):
        if len(v) > 10:
            raise ValueError('Número tem que ter menos que 10 caracteres')
        return v

    @classmethod
    @field_validator('complemento')
    def validate_complemento(cls, v):
        if len(v) > 100:
            raise ValueError('Complemento tem que ter menos que 100 caracteres')
        return v

    @classmethod
    @field_validator('municipio')
    def validate_municipio(cls, v):
        if len(v) > 100:
            raise ValueError('Município tem que ter menos que 30 caracteres')
        return v

    @classmethod
    @field_validator('uf')
    def validate_uf(cls, v):
        if len(v) > 2:
            raise ValueError('UF tem que ter menos que 2 caracteres')
        return v

    @classmethod
    @field_validator('cep')
    def validate_cep(cls, v):
        if len(v) > 8:
            raise ValueError('CEP tem que ter menos que 2 caracteres')
        return v

    @classmethod
    @field_validator('bairro')
    def validate_bairro(cls, v):
        if len(v) > 30:
            raise ValueError('Bairro tem que ter menos que 30 caracteres')
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
    dados_etiqueta: DadosEtiquetaParser | None = None

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


class ItemParser(BaseModel):
    descricao: str
    un: str
    qtde: Decimal
    vlr_unit: Decimal
    tipo: str

    @classmethod
    @field_validator('tipo')
    def validate_tipo(cls, v):
        tipos = ['P', 'S']
        if v not in tipos:
            raise ValueError(f'Tipo invalido escolha uma opção {tipos}')
        return v


class XMLParser(BaseModel):
    cliente: list[ClientParser]
    transporte: list[TransporteParser]
    itens: list[ItemParser]
