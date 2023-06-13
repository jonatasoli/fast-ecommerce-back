import requests
from loguru import logger

from .adapter import Adapter


def correios_zip_code():
    url = 'https://apps.correios.com.br/SigepMasterJPA/AtendeClienteService/AtendeCliente?wsdl'
    return url


def correios_shipping():
    url = 'http://ws.correios.com.br/calculador/CalcPrecoPrazo.asmx?wsdl'
    return url


class FindZipCode:
    def __init__(self, zip_code_target):
        self.zip_code_target = zip_code_target

    def find_zip_code_target(self, url=correios_zip_code()):
        headers = {'content-type': 'text/xml; charset=utf-8'}
        body = Adapter.xml_find_zipcode(self.zip_code_target)
        response = requests.post(url, headers=headers, data=body)
        content = response.content
        if response.status_code == 200:
            data = Adapter.xmltojson_consultacep(content)
            return data
        return {'message': 'Cep inválido'}


class CalculateShipping:
    def __init__(
        self, zip_code_source, zip_code_target, weigth, length, heigth, width
    ):
        self.zip_code_source = zip_code_source
        self.zip_code_target = zip_code_target
        self.weigth = weigth
        self.length = length
        self.heigth = heigth
        self.width = width

    def calculate_shipping(self, url=correios_shipping()):
        services = ['4510', '4014']
        shipping_list = []
        for service in services:
            headers = {'content-type': 'text/xml; charset=utf-8'}
            body = Adapter.body_shipping(
                service,
                self.zip_code_source,
                self.zip_code_target,
                self.weigth,
                self.length,
                self.heigth,
                self.width,
            )
            response = requests.post(url, headers=headers, data=body)
            content = response.content
            logger.debug(content)
            if '4510' == service:
                name = 'PAC'
            if '4014' == service:
                name = 'SEDEX'
            result = Adapter.xmltojson_shipping(content, name)
            result['frete'] = int((result['frete'].replace(',', '')))
            shipping_list.append(result)
        return shipping_list
