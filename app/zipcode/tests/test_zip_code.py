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
    shipping = CalculateShipping('07171140','47590000','0.5', '2.5', '0', '3.0')
    shipping = shipping.calculate_shipping()
    assert next(shipping) == {
        'frete':'35,40',
        'prazo':'12',
        'serviço':'PAC'
    }

    
