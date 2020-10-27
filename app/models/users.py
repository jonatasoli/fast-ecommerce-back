from sqlalchemy.orm import backref, relationship
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean
from passlib.hash import pbkdf2_sha512
from loguru import logger

from constants import DocumentType
from ext.database import Base


class User(Base):
    id = Column(Integer, nullable=False, primary_key=True)
    name = Column(String(512))

    # picture_id = Column(String(512), ForeignKey("uploaded_image.id"))
    # picture = relationship("UploadedImage", backref=backref("user", uselist=False), foreign_keys=[picture_id],
                              # uselist=False)

    document = Column(String(32), unique=True)
    document_type = Column(String(32), default=DocumentType.CPF.value, server_default=DocumentType.CPF.value)
    birth_date = Column(DateTime, nullable=True)
    gender = Column(String(32), nullable=True)
    email = Column(String(128), unique=True)
    phone = Column(String(128), nullable=True)
    user_timezone = Column(String(50), default='America/Sao_Paulo', server_default='America/Sao_Paulo',
                              nullable=True)
    password = Column(String)

    role_id = Column(Integer, ForeignKey("role.id"))

    status = Column(String(20), default="deactivated")

    update_email_on_next_login = Column(Boolean, default=False, server_default='0')
    update_password_on_next_login = Column(Boolean, default=False, server_default='0')

    def to_app_json(self, expand=False):
        return {
            'id': self.id,
            'name': self.name,
            'picture_id': self.picture_id,
            'profile_picture': self.user_profile_picture(),
            'document': self.document,
            'gender': self.gender,
            'email': self.email,
            'phone': self.phone,
            'user_timezone': self.user_timezone,
            'role': self.role,
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
            role=None,
            update_email_on_next_login=False,
            update_password_on_next_login=False
    ):
        super().__init__()
        self.name = name
        self.document_type = document_type
        self.document = document
        self.birth_date = birth_date
        self.email = email
        self.phone = phone
        self.role = role

        self.update_email_on_next_login = update_email_on_next_login
        self.update_password_on_next_login = update_password_on_next_login
        logger.info(f"A senha é {password}")
        if password is not None:
            self.gen_hash(password)

    def gen_hash(self, password):
        self.password = pbkdf2_sha512.hash(password)

    def verify_password(self, password):
        return pbkdf2_sha512.verify(password, self.password)


class Address(Base):
    id = Column(Integer, nullable=False, primary_key=True)
    user_id = Column(Integer, ForeignKey("user.id"))
    user = relationship("User", foreign_keys=[user_id], backref="payments", cascade="all,delete",
            uselist=False)
    type_address=Column(String)
    category=Column(String)
    country = Column(String(58))
    city = Column(String(58))
    state = Column(String(58))
    neighborhood = Column(String(58))
    street = Column(String)
    street_number = Column(String)
    address_complement = Column(String)
    zipcode = Column(String)

    def to_json(self):
        return {
                "country": self.country,
                "city": self.city,
                "state": self.state,
                "neighborhood": self.neighborhood,
                "street": self.street,
                "street_number": self.street_number,
                "zipcode": self.zipcode
                }
