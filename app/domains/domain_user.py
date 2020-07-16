from sqlalchemy.orm import Session
from sqlalchemy import and_

from schemas.user_schema import SignUp, Login, AddressSchema
from schemas.order_schema import CheckoutSchema
from models.users import User, Address
from constants import DocumentType, Roles


def create_user(db: Session, obj_in: SignUp):
    try:

        db_user = User(
                name=obj_in.name,
                document_type=DocumentType.CPF.value,
                document=obj_in.document,
                birth_date=None,
                email=obj_in.mail,
                phone=obj_in.phone,
                password=obj_in.password.get_secret_value(),
                role=Roles.USER.value,
                update_email_on_next_login=False,
                update_password_on_next_login=False
                )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    except Exception as e:
        raise e


def check_existent_user(db: Session, email, document, password):
    try:
        db_user = db.query(User).filter_by(document=document).first()
        if not password:
            raise Exception('User not password')
        if db_user and db_user.verify_password(password.get_secret_value()):
            return db_user
        else:
            return None
    except Exception as e:
        raise e


def authenticate(db: Session, user: Login):
    try:

        db_user = db.query(User).filter_by(document=user.document).first()
        if not user.password:
            raise Exception('User not password')
        if db_user and db_user.verify_password(user.password.get_secret_value()):
            return db_user
        else:
            raise Exception(f'User not finded {user.document}, {user.password}')

    except Exception as e:
        raise e


def register_payment_address(db: Session, checkout_data: CheckoutSchema, user):
    try:
        _address = db.query(Address).filter(and_(
            Address.user_id==user.id,
            Address.zipcode==checkout_data.zip_code,
            Address.street_number==checkout_data.address_number,
            Address.address_complement==checkout_data.address_complement,
            Address.category=='billing')
            ).first()

        if not _address:
            db_payment_address = Address(
                    user_id=user.id,
                    country=checkout_data.country,
                    city=checkout_data.city,
                    state=checkout_data.state,
                    neighborhood=checkout_data.neighborhood,
                    street=checkout_data.address,
                    street_number=checkout_data.address_number,
                    zipcode=checkout_data.zip_code,
                    type_address='house',
                    category='billing'
                    )
            db.add(db_payment_address)
            db.commit()
            _address=db_payment_address
        return _address
    except Exception as e:
        raise e


def register_shipping_address(db: Session, checkout_data: CheckoutSchema, user):
    try:
        _address = db.query(Address).filter(and_(
            Address.user_id==user.id,
            Address.zipcode==checkout_data.ship_zip,
            Address.street_number==checkout_data.ship_number,
            Address.address_complement==checkout_data.ship_address_complement,
            Address.category=='shipping')
            ).first()

        if not _address:
            db_shipping_address = Address(
                    user_id=user.id,
                    country=checkout_data.ship_country,
                    city=checkout_data.ship_city,
                    state=checkout_data.ship_state,
                    neighborhood=checkout_data.ship_neighborhood,
                    street=checkout_data.ship_address,
                    street_number=checkout_data.ship_number,
                    zipcode=checkout_data.ship_zip,
                    type_address='house',
                    category='shipping'
                    )
            db.add(db_shipping_address)
            db.commit()
            _address=db_shipping_address
        return _address
    except Exception as e:
        raise e
