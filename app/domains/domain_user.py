import httpx
import enum
from functools import wraps
from dynaconf import settings
from loguru import logger
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import and_

from jose import JWTError, jwt
from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext

from schemas.user_schema import (
    SignUp,
    UserInDB,
    UserSchema,
)
from ext.database import get_session
from schemas.order_schema import CheckoutSchema
from models.users import User, Address
from models.role import Role
from constants import DocumentType, Roles


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="access_token")


class COUNTRY_CODE(enum.Enum):
    brazil = 'brazil'


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
            role_id=Roles.USER.value,
            update_email_on_next_login=False,
            update_password_on_next_login=False,
        )
        db.add(db_user)
        logger.info(db_user)
        db.commit()
        return db_user
    except Exception as e:
        db.rollback()
        logger.error(e)
        raise e


def check_existent_user(db: Session, email, document, password):
    try:
        db_user = db.query(User).filter_by(document=document).first()
        if not password:
            raise Exception("User not password")
        # if db_user and db_user.verify_password(password.get_secret_value()):
        #     return db_user
        logger.info("---------DB_USER-----------")
        logger.info(f"DB_USER -> {db_user}")
        return db_user
    except Exception as e:
        raise e


def get_user(db: Session, document: str, password: str):
    try:

        db_user = _get_user(db=db, document=document)
        if not password:
            raise Exception("User not password")
        if db_user and db_user.verify_password(password):
            return db_user
        else:
            raise Exception(
                f"User not finded {db_user.document}, {db_user.password}"
            )

    except Exception as e:
        raise e


def authenticate_user(db, document: str, password: str):
    user = get_user(db, document, password)
    user_dict = UserSchema.from_orm(user).dict()

    user = UserInDB(**user_dict)
    logger.debug(f"{user} ")
    if not user:
        return False
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def get_current_user(
    token: str,
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        document: str = payload.get("sub")
        if document is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    db = get_session()()

    user = _get_user(db, document=document)
    if user is None:
        raise credentials_exception
    return user


def _get_user(db: Session, document: str):
    try:

        return db.query(User).filter_by(document=document).first()

    except Exception as e:
        raise e


def check_token(f):
    @wraps(f)
    def check_jwt(
        *args,
        **kwargs
    ):
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        try:
            payload = jwt.decode(
                kwargs.get('token', None),
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM]
            )
            _user_credentials: str = payload.get("sub")
            if not payload or _user_credentials is None:
                raise credentials_exception
        except JWTError:
            raise credentials_exception
        return f(*args, **kwargs)
    return check_jwt


def get_role_user(db: Session, user_role_id: int):
    _role = db.query(Role).filter_by(id=user_role_id).first()
    return _role.role


def register_payment_address(db: Session, checkout_data: CheckoutSchema, user):
    try:
        _address = (
            db.query(Address)
            .filter(
                and_(
                    Address.user_id == user.id,
                    Address.zipcode == checkout_data.get("zip_code"),
                    Address.street_number
                    == checkout_data.get("address_number"),
                    Address.address_complement
                    == checkout_data.get("address_complement"),
                    Address.category == "billing",
                )
            )
            .first()
        )
        if not _address:
            db_payment_address = Address(
                user_id=user.id,
                country=checkout_data.get("country"),
                city=checkout_data.get("city"),
                state=checkout_data.get("state"),
                neighborhood=checkout_data.get("neighborhood"),
                street=checkout_data.get("address"),
                street_number=checkout_data.get("address_number"),
                zipcode=checkout_data.get("zip_code"),
                type_address="house",
                category="billing",
            )
            db.add(db_payment_address)
            db.commit()
            _address = db_payment_address
        return _address
    except Exception as e:
        db.rollback()
        raise e


def register_shipping_address(
    db: Session,
    checkout_data: CheckoutSchema,
    user
):
    try:
        _address = (
            db.query(Address)
            .filter(
                and_(
                    Address.user_id == user.id,
                    Address.zipcode == checkout_data.get("ship_zip"),
                    Address.street_number == checkout_data.get("ship_number"),
                    Address.address_complement == checkout_data.get(
                        "ship_address_complement"
                    ),
                    Address.category == "shipping",
                )
            )
            .first()
        )

        if checkout_data.get("shipping_is_payment"):
            logger.debug(f"{checkout_data}")
            if not checkout_data.get("ship_zip"):
                _address = (
                    db.query(Address)
                    .filter(
                        and_(
                            Address.user_id == user.id,
                            Address.zipcode == checkout_data.get("zip_code"),
                            Address.street_number
                            == checkout_data.get("address_number"),
                            Address.address_complement
                            == checkout_data.get("address_complement"),
                            Address.category == "billing",
                        )
                    )
                    .first()
                )
            if not _address:
                db_shipping_address = Address(
                    user_id=user.id,
                    country=checkout_data.get("country"),
                    city=checkout_data.get("city"),
                    state=checkout_data.get("state"),
                    neighborhood=checkout_data.get("neighborhood"),
                    street=checkout_data.get("address"),
                    street_number=checkout_data.get("address_number"),
                    zipcode=checkout_data.get("zip_code"),
                    type_address="house",
                    category="shipping",
                )
                db.add(db_shipping_address)
                db.commit()
                _address = db_shipping_address
        else:

            if not _address:
                db_shipping_address = Address(
                    user_id=user.id,
                    country=checkout_data.get("ship_country"),
                    city=checkout_data.get("ship_city"),
                    state=checkout_data.get("ship_state"),
                    neighborhood=checkout_data.get("ship_neighborhood"),
                    street=checkout_data.get("ship_address"),
                    street_number=checkout_data.get("ship_number"),
                    zipcode=checkout_data.get("ship_zip"),
                    type_address="house",
                    category="shipping",
                )
                db.add(db_shipping_address)
                db.commit()
                _address = db_shipping_address

        logger.debug("INFO")
        logger.error(f"{_address}")
        return _address
    except Exception as e:
        db.rollback()
        raise e


def address_by_postal_code(zipcode_data):
    try:

        postal_code = zipcode_data.get("postal_code")

        if not postal_code:
            return HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                details={"message": "Cep inválido"})

        viacep_url = f"https://viacep.com.br/ws/{postal_code}/json/"
        status_code = httpx.get(viacep_url).status_code

        if status_code != 200:
            return HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"message": "Cep inválido"})

        response = httpx.get(viacep_url).json()

        if response.get("erro"):
            return HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                details={"message": "Cep inválido"})

        address = {
            "street": response.get("logradouro"),
            "city": response.get("localidade"),
            "neighborhood": response.get("bairro"),
            "state": response.get("uf"),
            "country": COUNTRY_CODE.brazil.value,
            "zip_code": postal_code,
        }

        return address

    except Exception as e:
        raise e
