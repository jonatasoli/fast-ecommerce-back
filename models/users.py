from loguru import logger
from passlib.context import CryptContext
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String

from constants import DocumentType
from ext.database import Base

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')


class User(Base):
    id = Column(Integer, nullable=False, primary_key=True)
    name = Column(String(512))

    #   "UploadedImage",
    #       "user",
    #   ), foreign_keys=[picture_id],
    # uselist=False)

    document = Column(String(32), unique=True)
    document_type = Column(
        String(32),
        default=DocumentType.CPF.value,
        server_default=DocumentType.CPF.value,
    )
    birth_date = Column(DateTime, nullable=True)
    gender = Column(String(32), nullable=True)
    email = Column(String(128), unique=True)
    phone = Column(String(128), nullable=True)
    user_timezone = Column(
        String(50),
        default='America/Sao_Paulo',
        server_default='America/Sao_Paulo',
        nullable=True,
    )
    password = Column(String)

    role_id = Column(Integer)

    status = Column(String(20), default='deactivated')
    uuid = Column(String, nullable=True)
    franchise_id = Column(Integer, default=1)

    update_email_on_next_login = Column(
        Boolean,
        default=False,
        server_default='0',
    )
    update_password_on_next_login = Column(
        Boolean,
        default=False,
        server_default='0',
    )

    def to_app_json(self, expand=False):
        return {
            'id': self.id,
            'uuid': self.uuid,
            'name': self.name,
            'picture_id': self.picture_id,
            'profile_picture': self.user_profile_picture(),
            'document': self.document,
            'gender': self.gender,
            'email': self.email,
            'phone': self.phone,
            'user_timezone': self.user_timezone,
            'role_id': self.role_id,
            'status': self.status,
            'terms_and_conditions_id': self.terms_and_conditions_id,
        }

    def __init__(
        self,
        name=None,
        document_type=None,
        document=None,
        birth_date=None,
        email=None,
        phone=None,
        password=None,
        role_id=None,
        update_email_on_next_login=False,
        update_password_on_next_login=False,
    ) -> None:
        super().__init__()
        self.name = name
        self.document_type = document_type
        self.document = document
        self.birth_date = birth_date
        self.email = email
        self.phone = phone
        self.role_id = role_id

        self.update_email_on_next_login = update_email_on_next_login
        self.update_password_on_next_login = update_password_on_next_login
        logger.info(f'A senha é {password}')
        if password is not None:
            self.gen_hash(password)

    def gen_hash(self, password):
        self.password = pwd_context.hash(password)

    def verify_password(self, password):
        return pwd_context.verify(password, self.password)


class Address(Base):
    id = Column(Integer, nullable=False, primary_key=True)
    user_id = Column(Integer)
    type_address = Column(String)
    category = Column(String)
    country = Column(String(58))
    city = Column(String(58))
    state = Column(String(58))
    neighborhood = Column(String(58))
    street = Column(String)
    street_number = Column(String)
    address_complement = Column(String)
    zipcode = Column(String)
    uuid = Column(String)
    active = Column(Boolean, default=False)

    def to_json(self):
        return {
            'country': self.country,
            'city': self.city,
            'state': self.state,
            'neighborhood': self.neighborhood,
            'street': self.street,
            'street_number': self.street_number,
            'zipcode': self.zipcode,
        }


class UserResetPassword(Base):
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    token = Column(String)
    used_token = Column(Boolean, default=False)
