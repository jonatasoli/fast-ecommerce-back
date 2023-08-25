import httpx
from loguru import logger

from .adapter import Adapter


def correios_zip_code():
    return 'https://apps.correios.com.br/SigepMasterJPA/AtendeClienteService/AtendeCliente?wsdl'


def correios_shipping():
    return 'http://ws.correios.com.br/calculador/CalcPrecoPrazo.asmx?wsdl'


class FindZipCode:
    def __init__(self, zip_code_target) -> None:
        self.zip_code_target = zip_code_target

    def find_zip_code_target(self, url=correios_zip_code()):
        headers = {'content-type': 'text/xml; charset=utf-8'}
        body = Adapter.xml_find_zipcode(self.zip_code_target)
        response = httpx.post(url, headers=headers, data=body)
        content = response.content
        if response.status_code == 200:
            return Adapter.xmltojson_consultacep(content)
        return {'message': 'Cep inválido'}


class CalculateShipping:
    def __init__(
        self,
        zip_code_source,
        zip_code_target,
        weigth,
        length,
        heigth,
        width,
    ) -> None:
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
            response = httpx.post(url, headers=headers, data=body)
            content = response.content
            logger.debug(content)
            if service == '4510':
                name = 'PAC'
            if service == '4014':
                name = 'SEDEX'
            result = Adapter.xmltojson_shipping(content, name)
            result['frete'] = int(result['frete'].replace(',', ''))
            shipping_list.append(result)
        return shipping_list
