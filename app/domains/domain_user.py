from dynaconf import settings
from loguru import logger
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import and_

from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext

from schemas.user_schema import SignUp, Login, AddressSchema, Token,\
        UserInDB
from schemas.order_schema import CheckoutSchema
from models.users import User, Address
from constants import DocumentType, Roles


fake_users_db = {
    "johndoe": {
        "username": "johndoe",
        "full_name": "John Doe",
        "email": "johndoe@example.com",
        "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
        "disabled": False,
    }
}

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def create_user(db: Session, obj_in: SignUp):
    try:
        logger.info(obj_in)
        logger.debug(Roles.USER.value)

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
        logger.info(db_user)
        db.commit()
        return db_user
    except Exception as e:
        logger.error(e)
        raise e


def check_existent_user(db: Session, email, document, password):
    try:
        db_user = db.query(User).filter_by(document=document).first()
        if not password:
            raise Exception('User not password')
        # if db_user and db_user.verify_password(password.get_secret_value()):
        #     return db_user
        logger.info("---------DB_USER-----------")
        logger.info(f"DB_USER -> {db_user}")
        return db_user
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


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def authenticate_user(fake_db, username: str, password: str):
    user = get_user(fake_db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def get_user(db, username: str):
    if username in db:
        user_dict = db[username]
        return UserInDB(**user_dict)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
            to_encode,
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = get_user(fake_users_db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = get_user(fake_users_db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


def register_payment_address(db: Session, checkout_data: CheckoutSchema, user):
    try:
        _address = db.query(Address).filter(and_(
            Address.user_id==user.id,
            Address.zipcode==checkout_data.get('zip_code'),
            Address.street_number==checkout_data.get('address_number'),
            Address.address_complement==checkout_data.get('address_complement'),
            Address.category=='billing')
            ).first()
        if not _address:
            db_payment_address = Address(
                    user_id=user.id,
                    country=checkout_data.get('country'),
                    city=checkout_data.get('city'),
                    state=checkout_data.get('state'),
                    neighborhood=checkout_data.get('neighborhood'),
                    street=checkout_data.get('address'),
                    street_number=checkout_data.get('address_number'),
                    zipcode=checkout_data.get('zip_code'),
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
            Address.zipcode==checkout_data.get('ship_zip'),
            Address.street_number==checkout_data.get('ship_number'),
            Address.address_complement==checkout_data.get('ship_address_complement'),
            Address.category=='shipping')
            ).first()

        if checkout_data.get('shipping_is_payment'):
            logger.debug(f"{checkout_data}")
            if not checkout_data.get('ship_zip'):
                _address = db.query(Address).filter(and_(
                    Address.user_id==user.id,
                    Address.zipcode==checkout_data.get('zip_code'),
                    Address.street_number==checkout_data.get('address_number'),
                    Address.address_complement==checkout_data.get('address_complement'),
                    Address.category=='billing')
                    ).first()
            if not _address:
                db_shipping_address = Address(
                        user_id=user.id,
                        country=checkout_data.get('country'),
                        city=checkout_data.get('city'),
                        state=checkout_data.get('state'),
                        neighborhood=checkout_data.get('neighborhood'),
                        street=checkout_data.get('address'),
                        street_number=checkout_data.get('address_number'),
                        zipcode=checkout_data.get('zip_code'),
                        type_address='house',
                        category='shipping'
                        )
                db.add(db_shipping_address)
                db.commit()
                _address=db_shipping_address
        else:

            if not _address:
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
                        category='shipping'
                        )
                db.add(db_shipping_address)
                db.commit()
                _address=db_shipping_address


        logger.debug("INFO")
        logger.error(f"{_address}")
        return _address
    except Exception as e:
        raise e


def address_by_postal_code(zipcode_data):
    try:

        postal_code = zipcode_data.get("postal_code")

        if not postal_code:
            return jsonify({"message": "Cep inválido"}), 400

        viacep_url = f"https://viacep.com.br/ws/{postal_code}/json/"
        status_code = requests.get(viacep_url).status_code

        if status_code != 200:
            return jsonify({"message": "Cep inválido"}), 400

        response = requests.get(viacep_url).json()

        if response.get("erro"):
            return jsonify({"message": "Cep inválido"}), 400

        address = { 
                "street": response.get('logradouro'),
                "city":response.get('localidade'),
                "neighborhood":response.get('bairro'),
                "state":response.get('uf'),
                "country":COUNTRY_CODE.brazil.value,
                "zip_code":postal_code
        }

        return address

    except Exception as e:
        raise e
