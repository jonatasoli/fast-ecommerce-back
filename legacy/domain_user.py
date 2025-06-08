import httpx
from fastapi import HTTPException, status
from loguru import logger
from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app.infra.models import AddressDB
from app.entities.order import CheckoutSchema


def register_payment_address(db: Session, checkout_data: CheckoutSchema, user):
    try:
        _address = None
        with db:
            address_query = select(AddressDB).where(
                and_(
                    AddressDB.user_id == user.id,
                    AddressDB.zipcode == checkout_data.get('zip_code'),
                    AddressDB.street_number
                    == checkout_data.get('address_number'),
                    AddressDB.address_complement
                    == checkout_data.get('address_complement'),
                    AddressDB.category == 'billing',
                ),
            )
            _address = db.execute(address_query).scalars().first()
            if not _address:
                db_payment_address = AddressDB(
                    user_id=user.id,
                    country=checkout_data.get('country'),
                    city=checkout_data.get('city'),
                    state=checkout_data.get('state'),
                    neighborhood=checkout_data.get('neighborhood'),
                    street=checkout_data.get('address'),
                    street_number=checkout_data.get('address_number'),
                    zipcode=checkout_data.get('zip_code'),
                    type_address='house',
                    category='billing',
                )
                db.add(db_payment_address)
                db.commit()
                _address = db_payment_address
        return _address
    except Exception:
        raise


def register_shipping_address(
    db: Session,
    checkout_data: CheckoutSchema,
    user,
):
    try:
        _address = None
        with db:
            address_query = select(AddressDB).where(
                and_(
                    AddressDB.user_id == user.id,
                    AddressDB.zipcode == checkout_data.get('ship_zip'),
                    AddressDB.street_number
                    == checkout_data.get('ship_number'),
                    AddressDB.address_complement
                    == checkout_data.get('ship_address_complement'),
                    AddressDB.category == 'shipping',
                ),
            )
            _address = db.execute(address_query).scalars().first()

            if checkout_data.get('shipping_is_payment'):
                logger.debug(f'{checkout_data}')
                if not checkout_data.get('ship_zip'):
                    address_query = select(AddressDB).where(
                        and_(
                            AddressDB.user_id == user.id,
                            AddressDB.zipcode == checkout_data.get('zip_code'),
                            AddressDB.street_number
                            == checkout_data.get('address_number'),
                            AddressDB.address_complement
                            == checkout_data.get('address_complement'),
                            AddressDB.category == 'billing',
                        ),
                    )
                    _address = db.execute(address_query).scalars().first()

                if not _address:
                    db_shipping_address = AddressDB(
                        user_id=user.id,
                        country=checkout_data.get('country'),
                        city=checkout_data.get('city'),
                        state=checkout_data.get('state'),
                        neighborhood=checkout_data.get('neighborhood'),
                        street=checkout_data.get('address'),
                        street_number=checkout_data.get('address_number'),
                        zipcode=checkout_data.get('zip_code'),
                        type_address='house',
                        category='shipping',
                    )
                    db.add(db_shipping_address)
                    db.commit()
                    _address = db_shipping_address
            elif not _address:
                db_shipping_address = Address(
                    user_id=user.id,
                    country=checkout_data.get('ship_country'),
                    city=checkout_data.get('ship_city'),
                    state=checkout_data.get('ship_state'),
                    neighborhood=checkout_data.get('ship_neighborhood'),
                    street=checkout_data.get('ship_address'),
                    street_number=checkout_data.get('ship_number'),
                    zipcode=checkout_data.get('ship_zip'),
                    type_address='house',
                    category='shipping',
                )
                db.add(db_shipping_address)
                db.commit()
                _address = db_shipping_address

            logger.debug('INFO')
            logger.error(f'{_address}')
        return _address
    except Exception:
        raise


def address_by_postal_code(zipcode_data):
    try:

        postal_code = zipcode_data.get('postal_code')

        if not postal_code:
            return HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                details={'message': 'Cep inválido'},
            )

        viacep_url = f'https://viacep.com.br/ws/{postal_code}/json/'
        status_code = httpx.get(viacep_url).status_code

        if status_code != 200:
            return HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={'message': 'Cep inválido'},
            )

        response = httpx.get(viacep_url).json()

        if response.get('erro'):
            return HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                details={'message': 'Cep inválido'},
            )

        return {
            'street': response.get('logradouro'),
            'city': response.get('localidade'),
            'neighborhood': response.get('bairro'),
            'state': response.get('uf'),
            'country': COUNTRY_CODE.brazil.value,
            'zip_code': postal_code,
        }

    except Exception:
        raise
