import pytest
from zipcode.zip_code import FindZipCode, CalculateShipping

def test_find_zip_code():
    cep = FindZipCode('07171140')
    assert cep.find_zip_code_target() == {
        'bairro': 'Jardim Presidente Dutra',
        'cep': '07171140',
        'cidade': 'Guarulhos',
        'complemento2': '',
        'end': 'Rua Maria Paula Motta',
        'uf': 'SP',
        'unidadePostagem': []
    }

def test_calculate_shipping():
    shipping = CalculateShipping('07171140','47590000','5', '15', '1', '10')
    shipping = shipping.calculate_shipping()
    assert next(shipping) == {
        'frete':'61,30',
        'prazo':'9',
        'serviço':'PAC'
    }

    
