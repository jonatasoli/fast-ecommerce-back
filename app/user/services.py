# ruff: noqa: ANN003, ANN002, ANN202, DTZ003, TRY302, TRY002, TRY201, TRY301, ANN001, RET505, TRY300, PLR0124 ARG001, N801, E501
import enum
from datetime import datetime, timedelta
from functools import wraps

from dynaconf import settings
from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from loguru import logger
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.orm import Session

from constants import DocumentType, Roles
from ext.database import get_session
from models.role import Role
from models.users import User, UserResetPassword
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


def create_user(db: Session, obj_in: SignUp) -> User:
    """Create user."""
    try:
        logger.info(obj_in)
        logger.debug(Roles.USER.value)

        with db:
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
        logger.error(e)
        raise e


def check_existent_user(db: Session, email, document, password) -> User:
    """Check existent user."""
    try:
        with db:
            user_query = select(User).where(document == document)
            db_user = db.execute(user_query).scalars().first()
        if not password:
            msg = 'User not password'
            raise Exception(msg)
        logger.info('---------DB_USER-----------')
        logger.info(f'DB_USER -> {db_user}')
        return db_user
    except Exception as e:
        raise e


def get_user(db: Session, document: str, password: str) -> UserInDB:
    """Get user."""
    try:
        db_user = _get_user(db=db, document=document)
        if not password:
            msg = 'User not password'
            raise Exception(msg)
        if db_user and db_user.verify_password(password):
            return db_user
        else:
            logger.error(
                f'User not finded {db_user.document}, {db_user.password}',
            )
            msg = f'User not finded {db_user.document}'
            raise Exception(msg)
    except Exception as e:
        raise e


def authenticate_user(db, document: str, password: str) -> UserInDB:
    """Authenticate user."""
    user = get_user(db, document, password)
    user_dict = UserSchema.model_validate(user).model_dump()

    user = UserInDB(**user_dict)
    logger.debug(f'{user} ')
    if not user:
        return False
    return user


def create_access_token(
    data: dict,
    expires_delta: timedelta | None = None,
) -> str:
    """Create access token."""
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
) -> User:
    """Must return user db."""
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


def _get_user(db: Session, document: str) -> User:
    """Must return user db."""
    with db:
        user_query = select(User).where(User.document == document)
        return db.execute(user_query).scalars().first()


def check_token(f) -> callable:
    """Check token."""

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
            _user_credentials: str = payload.get('sub')
            if not payload or _user_credentials is None:
                raise credentials_exception
        except JWTError:
            raise credentials_exception
        return f(*args, **kwargs)

    return check_jwt


def get_role_user(db: Session, user_role_id: int) -> str:
    """Must return role user."""
    with db:
        role_query = select(Role).where(Role.id == user_role_id)
        _role = db.execute(role_query).scalars().first()
        return _role.role


def get_user_login(db: Session, document: str) -> UserSchema:
    """Must return user login."""
    with db:
        user_query = select(User).where(User.document == document)
        user_db = db.execute(user_query).scalars().first()
    return UserSchema.model_validate(user_db)


def save_token_reset_password(db: Session, document: str) -> UserResetPassword:
    """Must save token reset password."""
    access_token_expires = timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
    )
    _token = create_access_token(
        data={'sub': document},
        expires_delta=access_token_expires,
    )
    with db:
        user_query = select(User).where(User.document == document)
        _user = db.execute(user_query).scalars().first()
        db_reset = UserResetPassword(user_id=_user.id, token=_token)
        db.add(db_reset)
        db.commit()
    return db_reset


def reset_password(db: Session, data: UserResponseResetPassword) -> None:
    """Must reset password."""
    pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
    with db:
        user_query = select(User).where(User.document == data.document)
        _user = db.execute(user_query).scalars().first()

        used_token_query = select(UserResetPassword).where(
            UserResetPassword.user_id == _user.id,
        )
        _used_token = db.execute(used_token_query).scalars().first()

        _used_token.used_token = True
        _user.password = pwd_context.hash(data.password)
        db.commit()
