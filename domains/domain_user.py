import enum
from datetime import datetime, timedelta
from functools import wraps

import httpx
from dynaconf import settings
from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from loguru import logger
from passlib.context import CryptContext
from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from constants import DocumentType, Roles
from app.infra.database import get_session
from app.infra.models import RoleDB
from app.infra.models import AddressDB, UserDB, UserResetPasswordDB
from schemas.order_schema import CheckoutSchema
from schemas.user_schema import (
    SignUp,
    UserInDB,
    UserResponseResetPassword,
    UserSchema,
)

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
oauth2_scheme = OAuth2PasswordBearer(tokenUrl='access_token')


class COUNTRY_CODE(enum.Enum):
    brazil = 'brazil'


def gen_hash(password):
    return pwd_context.hash(password)


def verify_password(password, check_password):
    return pwd_context.verify(check_password, password)


def create_user(db: Session, obj_in: SignUp):
    try:
        logger.info(obj_in)
        logger.debug(Roles.USER.value)
        if not obj_in.password:
            msg = 'User not password'
            raise Exception(msg)

        with db:
            db_user = UserDB(
                name=obj_in.name,
                username=obj_in.username,
                document_type=DocumentType.CPF.value,
                document=obj_in.document,
                birth_date=None,
                email=obj_in.mail,
                phone=obj_in.phone,
                password=gen_hash(obj_in.password.get_secret_value()),
                role_id=Roles.USER.value,
                update_email_on_next_login=False,
                update_password_on_next_login=False,
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
        with db:
            user_query = select(UserDB).where(UserDB.document == document)
            db_user = db.execute(user_query).scalars().first()
        if not password:
            msg = 'User not password'
            raise Exception(msg)
        logger.info('---------DB_USER-----------')
        logger.info(f'DB_USER -> {db_user}')
        return db_user
    except Exception as e:
        raise e


def get_user(db: Session, document: str, password: str):
    try:
        db_user = _get_user(db=db, document=document)
        if not password:
            msg = 'User not password'
            raise Exception(msg)
        if db_user and verify_password(db_user.password, password):
            return db_user
        else:
            logger.error(
                f'User not finded {db_user.document}, {db_user.password}',
            )
            raise HTTPException(status_code=403, detail='Access forbidden')
    except Exception as e:
        raise e


def authenticate_user(db, document: str, password: str):
    user = get_user(db, document, password)
    user_dict = UserSchema.model_validate(user).model_dump()

    user = UserInDB(**user_dict)
    logger.debug(f'{user} ')
    if not user:
        return False
    return user


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({'exp': expire})
    return jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )


def get_current_user(
    token: str,
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail='Could not validate credentials',
        headers={'WWW-Authenticate': 'Bearer'},
    )
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        document: str = payload.get('sub')
        if document is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    db = get_session()()

    user = _get_user(db, document=document)
    if user is None:
        raise credentials_exception
    return user


def get_affiliate(
    token: str,
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail='Could not validate credentials',
        headers={'WWW-Authenticate': 'Bearer'},
    )
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        document: str = payload.get('sub')
        if document is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    db = get_session()()

    user = _get_user(db, document=document)
    if user is None or user.role_id == Roles.USER.value:
        raise credentials_exception
    return user


def get_admin(
    token: str,
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail='Could not validate credentials',
        headers={'WWW-Authenticate': 'Bearer'},
    )
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        document: str = payload.get('sub')
        if document is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    db = get_session()()

    user = _get_user(db, document=document)
    if user is None or user.role_id != Roles.ADMIN.value:
        raise credentials_exception
    return user


def _get_user(db: Session, document: str):
    with db:
        user_query = select(UserDB).where(UserDB.document == document)
        return db.execute(user_query).scalars().first()


def check_token(f):
    @wraps(f)
    def check_jwt(*args, **kwargs):
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Could not validate credentials',
            headers={'WWW-Authenticate': 'Bearer'},
        )
        try:
            payload = jwt.decode(
                kwargs.get('token', None),
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM],
            )
            logger.info('Validação')
            logger.info(payload)
            _user_credentials: str = payload.get('sub')
            logger.info(_user_credentials)
            if not payload or _user_credentials is None:
                raise credentials_exception
        except JWTError:
            raise credentials_exception
        return f(*args, **kwargs)

    return check_jwt


def get_role_user(db: Session, user_role_id: int):
    with db:
        role_query = select(RoleDB).where(RoleDB.role_id == user_role_id)
        _role = db.scalar(role_query)
        return _role.role


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
    except Exception as e:
        raise e


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
                    AddressDB.street_number == checkout_data.get('ship_number'),
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
                        category='shipping',
                    )
                    db.add(db_shipping_address)
                    db.commit()
                    _address = db_shipping_address

            logger.debug('INFO')
            logger.error(f'{_address}')
        return _address
    except Exception as e:
        raise e


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

    except Exception as e:
        raise e


def get_user_login(db: Session, document: str):
    with db:
        user_query = select(UserDB).where(UserDB.document == document)
        user_db = db.execute(user_query).scalars().first()
    return UserSchema.from_orm(user_db)


def save_token_reset_password(db: Session, document: str):
    access_token_expires = timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
    )
    _token = create_access_token(
        data={'sub': document},
        expires_delta=access_token_expires,
    )
    with db:
        user_query = select(UserDB).where(UserDB.document == document)
        _user = db.execute(user_query).scalars().first()
        db_reset = UserResetPasswoDBrdDB(user_id=_user.id, token=_token)
        db.add(db_reset)
        db.commit()
    return db_reset


def reset_password(db: Session, data: UserResponseResetPassword):
    pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
    with db:
        user_query = select(UserDB).where(UserDB.document == data.document)
        _user = db.execute(user_query).scalars().first()

        used_token_query = select(UserResetPasswordDB).where(
            UserResetPasswordDB.user_id == _user.id,
        )
        _used_token = db.execute(used_token_query).scalars().first()

        _used_token.used_token = True
        _user.password = pwd_context.hash(data.password)
        db.commit()
    return 'Senha alterada'
