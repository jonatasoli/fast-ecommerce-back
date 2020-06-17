import enum


class DocumentType(enum.Enum):
    CPF = 'CPF'


class Roles(enum.Enum):
    ADMIN = 'ADMIN'
    USER = 'USER'
