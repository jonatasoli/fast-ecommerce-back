from bs4 import BeautifulSoup
from loguru import logger


class Adapter:
    def xml_find_zipcode(cep):
        return (
            """<x:Envelope
        xmlns:x="http://schemas.xmlsoap.org/soap/envelope/"
        xmlns:cli="http://cliente.bean.master.sigep.bsb.correios.com.br/">
        <x:Header/>
         <x:Body>
            <cli:consultaCEP>
                <cep>"""
            + cep
            + """</cep>
            </cli:consultaCEP>
        </x:Body>
        </x:Envelope>"""
        )

    def xmltojson_consultacep(xml):
        soup = BeautifulSoup(xml, 'lxml')
        return {
            'bairro': soup.bairro.text,
            'cep': soup.cep.text,
            'cidade': soup.cidade.text,
            'complemento2': soup.complemento2.text,
            'end': soup.end.text,
            'uf': soup.uf.text,
            'unidadePostagem': [],
        }

    def xmltojson_shipping(xml, name):
        soup = BeautifulSoup(xml, 'xml')
        return {
            'serviço': name,
            'frete': soup.Valor.text,
            'prazo': soup.PrazoEntrega.text,
        }

    def body_shipping(
        cod_service,
        zip_code_source,
        zip_code_target,
        weigth,
        length,
        heigth,
        width,
    ):
        body = (
            """<x:Envelope
        xmlns:x="http://schemas.xmlsoap.org/soap/envelope/"
        xmlns:tem="http://tempuri.org/">
        <x:Header/>
        <x:Body>
            <tem:CalcPrecoPrazo>
                <tem:nCdEmpresa></tem:nCdEmpresa>
                <tem:sDsSenha></tem:sDsSenha>
                <tem:nCdServico>"""
            + cod_service
            + """</tem:nCdServico>
                <tem:sCepOrigem>"""
            + zip_code_source
            + """</tem:sCepOrigem>
                <tem:sCepDestino>"""
            + zip_code_target
            + """</tem:sCepDestino>
                <tem:nVlPeso>"""
            + weigth
            + """</tem:nVlPeso>
                <tem:nCdFormato>1</tem:nCdFormato>
                <tem:nVlComprimento>"""
            + length
            + """</tem:nVlComprimento>
                <tem:nVlAltura>"""
            + heigth
            + """</tem:nVlAltura>
                <tem:nVlLargura>"""
            + width
            + """</tem:nVlLargura>
                <tem:nVlDiametro>0</tem:nVlDiametro>
                <tem:sCdMaoPropria>n</tem:sCdMaoPropria>
                <tem:nVlValorDeclarado>0</tem:nVlValorDeclarado>
                <tem:sCdAvisoRecebimento>n</tem:sCdAvisoRecebimento>
            </tem:CalcPrecoPrazo>
        </x:Body>
        </x:Envelope>"""
        )
        logger.debug(body)
        return body
