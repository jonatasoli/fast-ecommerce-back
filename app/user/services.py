# ruff: noqa: ANN401
import re
from datetime import UTC, datetime, timedelta
import enum
from functools import wraps
from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from loguru import logger
from passlib.context import CryptContext
from faststream.rabbit import RabbitQueue

from sqlalchemy import select, exc
from app.entities.user import (
    DocumentType,
    PasswordEmptyError,
    Roles,
    SignUp,
    SignUpResponse,
    UserCouponResponse,
    CredentialError,
    UserDuplicateError,
    UserInDB,
    UserNotFoundError,
    UserResponseResetPassword,
    UserSchema,
    UserUpdate,
)
from app.infra.models import RoleDB, UserDB, CouponsDB, UserResetPasswordDB
from jwt import DecodeError, encode, decode
from app.user import repository
from config import settings
from sqlalchemy.orm import Session, selectinload, sessionmaker


pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
oauth2_scheme = OAuth2PasswordBearer(tokenUrl='access_token')


class CountryCode(enum.StrEnum):
    brazil = 'brazil'


def gen_hash(password: str) -> str:
    """Gen pwd hash."""
    return pwd_context.hash(password)


def create_user(db, obj_in: SignUp) -> SignUpResponse:
    """Create User."""
    try:
        logger.info(obj_in)
        logger.debug(Roles.USER.value)
        if not obj_in.password:
            raise_password_empty_error()

        with db() as session:
            db_user = UserDB(
                name=obj_in.name,
                username=obj_in.username,
                document_type=DocumentType.CPF.value,
                document=re.sub(r'[^0-9]', '', obj_in.document),
                birth_date=None,
                email=obj_in.mail,
                phone=obj_in.phone,
                password=gen_hash(obj_in.password.get_secret_value()),
                role_id=Roles.USER.value,
                update_email_on_next_login=False,
                update_password_on_next_login=False,
                terms=obj_in.terms,
            )
            session.add(db_user)
            logger.info(db_user)
            session.commit()
    except exc.IntegrityError as err:
        raise UserDuplicateError from err
    except Exception as e:
        logger.error(e)
        raise
    else:
        return SignUpResponse(
            name=f'{db_user.name}',
            message='Add with sucesso!',
        )


def raise_password_empty_error() -> PasswordEmptyError:
    """Password Empty error raise."""
    raise PasswordEmptyError


def raise_user_not_found_error() -> UserNotFoundError:
    """User not found error raise."""
    raise UserNotFoundError


def raise_credential_error() -> CredentialError:
    """User with credentials wrong error raise."""
    raise CredentialError


def check_existent_user(db: Session, document: str, password: str) -> UserDB:
    """Check if user exist."""
    with db:
        user_query = select(UserDB).options(
            selectinload(UserDB.addresses)).where(
            UserDB.document == document,
        )
        db_user = db.execute(user_query).scalars().first()
    if not password:
        raise_password_empty_error()
    if not db_user:
        raise_user_not_found_error()
    logger.info('---------DB_USER-----------')
    logger.info(f'DB_USER -> {db_user}')
    return db_user


def get_affiliate(
    token: str,
    *,
    db: sessionmaker,
) -> UserSchema:
    """Return Afiliate user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail='Could not validate credentials',
        headers={'WWW-Authenticate': 'Bearer'},
    )
    try:
        payload = decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        document: str = payload.get('sub')
        if document is None:
            raise credentials_exception
    except DecodeError:
        raise_credential_error()

    user = _get_user_from_document(document, db=db)
    if user is None or user.role_id == Roles.USER.value:
        raise_credential_error()
    return user


async def get_affiliate_by_token(
    token: str,
    db,
) -> UserSchema:
    """Return Afiliate user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail='Could not validate credentials',
        headers={'WWW-Authenticate': 'Bearer'},
    )
    try:
        payload = decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        document: str = payload.get('sub')
        if document is None:
            raise credentials_exception
    except DecodeError:
        raise_credential_error()

    user = await _get_user_by_document(document, db=db)
    if user is None or user.role_id == Roles.USER.value:
        raise_credential_error()
    return user

def get_affiliate_urls(
    user: UserDB,
    db: Session,
    base_url: str,
) -> UserCouponResponse:
    """Get affiliate user and return code urls."""
    _urls = []
    with db() as transaction:
        coupons = transaction.query(CouponsDB).filter(
            CouponsDB.affiliate_id == user.user_id,
        )
        for coupon in coupons:
            _urls.append(f'{base_url}?coupon={coupon.code}')
    return UserCouponResponse(urls=_urls)


def get_current_user(
    token: str,
    *,
    db: sessionmaker,
) -> UserSchema:
    """Must return user db."""
    try:
        payload = decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        document = payload.get('sub')
        if document is None:
            raise CredentialError
    except DecodeError:
        raise CredentialError from DecodeError

    with db() as session:
        user = session.scalar(
            select(UserDB).options(
                selectinload(UserDB.addresses),
            ).where(UserDB.document == document),
        )
    if not user:
        raise CredentialError
    return UserSchema.model_validate(user)


def create_access_token(
    data: dict,
    expires_delta: timedelta | None = None,
) -> str:
    """Create temporary access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(tz=UTC) + expires_delta
    else:
        expire = datetime.now(tz=UTC) + timedelta(minutes=15)
    to_encode.update({'exp': expire})
    return encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )


async def save_token_reset_password(
    document: str,
    *,
    message,
    db,
) -> None:
    """Create request to reset password."""
    access_token_expires = timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
    )
    _token = create_access_token(
        data={'sub': document},
        expires_delta=access_token_expires,
    )
    with db() as session:
        user_query = select(UserDB).options(
            selectinload(UserDB.addresses),
        ).where(UserDB.document == document)
        _user = session.scalar(user_query)
        db_reset = UserResetPasswordDB(user_id=_user.user_id, token=_token)
        session.add(db_reset)
        session.commit()
        await message.broker.publish(
            {
                'mail_to': _user.email,
                'token': _token,
            },
            queue=RabbitQueue('reset_password_request'),
        )


def reset_password(
    token: str,
    *,
    db: sessionmaker,
    data: UserResponseResetPassword,
) -> None:
    """Reset password with token created."""
    pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
    with db() as session:
        user_query = select(UserDB).options(
            selectinload(UserDB.addresses),
        ).where(UserDB.document == data.document)
        _user = session.scalar(user_query)

        used_token_query = select(UserResetPasswordDB).where(
            UserResetPasswordDB.user_id == _user.user_id,
            UserResetPasswordDB.token == token,
        )
        _used_token = session.scalar(used_token_query)

        _used_token.used_token = True
        _user.password = pwd_context.hash(data.password)
        session.commit()


def verify_admin_sync():
    """Get admin user."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs): # noqa: ARG001
            try:
                payload = decode(
                    kwargs['token'],
                    settings.SECRET_KEY,
                    algorithms=[settings.ALGORITHM],
                )
                document: str = payload.get('sub')
                if document is None:
                    raise CredentialError
            except DecodeError:
                raise_credential_error()

            user = _get_user_from_document(document, db=kwargs['db'])
            if user is None or user.role_id != Roles.ADMIN.value:
                raise CredentialError
            return user
        return wrapper
    return decorator


def verify_admin_async():
    """Get admin user."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            credentials_exception = HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='Could not validate credentials',
                headers={'WWW-Authenticate': 'Bearer'},
            )
            try:
                payload = decode(
                    kwargs['token'],
                    settings.SECRET_KEY,
                    algorithms=[settings.ALGORITHM],
                )
                document: str = payload.get('sub')
                if not document:
                    raise credentials_exception
            except DecodeError:
                raise_credential_error()

            async with kwargs['db']() as session:
                user_query = select(UserDB).options(
                    selectinload(UserDB.addresses),
                ).where(UserDB.document == document)
                user_db = await session.scalar(user_query)
                if not user_db:
                    raise CredentialError
                user = UserSchema.model_validate(user_db)
            if user is None or user.role_id != Roles.ADMIN.value:
                raise credentials_exception
            return await func(*args, **kwargs)
        return wrapper
    return decorator


async def verify_admin(token: str, *, db):
    """Get admin user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail='Could not validate credentials',
        headers={'WWW-Authenticate': 'Bearer'},
    )
    try:
        payload = decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        document: str = payload.get('sub')
        if document is None:
            raise credentials_exception
    except DecodeError:
        raise_credential_error()

    async with db() as session:
        user_query = select(UserDB).options(
            selectinload(UserDB.addresses),
        ).where(UserDB.document == document)
        user_db = await session.scalar(user_query)
        if not user_db:
            raise CredentialError
        user = UserSchema.model_validate(user_db)
    if user is None or user.role_id != Roles.ADMIN.value:
        raise credentials_exception
    return user


def _get_user_from_document(document: str, *, db: sessionmaker) -> UserSchema:
    """Get user from database."""
    with db() as session:
        user_query = select(UserDB).options(
            selectinload(UserDB.addresses),
        ).where(UserDB.document == document)
        user_db = session.scalar(user_query)
        if not user_db:
            raise CredentialError
        return UserSchema.model_validate(user_db)


async def _get_user_by_document(document: str, *, db) -> UserSchema:
    """Get user from database."""
    async with db as session:
        user_query = select(UserDB).options(
            selectinload(UserDB.addresses),
        ).where(UserDB.document == document)
        user_db = await session.scalar(user_query)
        if not user_db:
            raise CredentialError
        return UserSchema.model_validate(user_db)


def check_token(f):
    """Annotation to check current jwt token is valid."""

    @wraps(f)
    def check_jwt(*args, **kwargs):
        """Check jwt token."""
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Could not validate credentials',
            headers={'WWW-Authenticate': 'Bearer'},
        )
        try:
            payload = decode(
                kwargs.get('token'),
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM],
            )
            logger.info('Validação')
            logger.info(payload)
            _user_credentials: str = payload.get('sub')
            logger.info(_user_credentials)
            if not payload or _user_credentials is None:
                raise credentials_exception
        except DecodeError:
            raise_credential_error()
        return f(*args, **kwargs)

    return check_jwt


def get_role_user(db: sessionmaker, user_role_id: int) -> str:
    """Get role by user."""
    with db() as session:
        role_query = select(RoleDB).where(RoleDB.role_id == user_role_id)
        _role = session.scalar(role_query)
    return _role.role


def authenticate_user(
    db: sessionmaker,
    document: str,
    password: str,
) -> UserInDB:
    """Authenticate user."""
    with db() as session:
        user_db = session.scalar(
            select(UserDB)
            .where(UserDB.document == document)
            .options(selectinload(UserDB.addresses)),
        )
        if not user_db or not verify_password(user_db.password, password):
            raise_credential_error()
    return UserInDB.model_validate(user_db)


def verify_password(password: str, check_password: str) -> bool:
    """Verify pasword if match with passed password."""
    _password_match = pwd_context.verify(check_password, password)
    if not _password_match:
        raise CredentialError
    return _password_match


async def update_user(
    user_id: int,
    *,
    update_user: UserUpdate,
    db,
) -> UserInDB:
    """Update user."""
    async with db().begin() as transaction:
        user_db = await repository.get_user_by_id(user_id, transaction=transaction)
        if not user_db:
            raise_credential_error()
        update_data = update_user.model_dump(exclude_none=True)
        for key, value in update_data.items():
            setattr(user_db, key, value)
        transaction.session.add(user_db)
        await transaction.session.commit()
    return UserInDB.model_validate(user_db)


async def get_user_by_id(
    user_id: int,
    *,
    db,
) -> UserInDB:
    """Update user."""
    async with db().begin() as transaction:
        user_db = await repository.get_user_by_id(user_id, transaction=transaction)
        if not user_db:
            raise_credential_error()
    return UserInDB.model_validate(user_db)
