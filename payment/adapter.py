from loguru import logger

from domains.domain_user import (
    check_existent_user,
    create_user,
)
from ext.database import get_session
from schemas.user_schema import SignUp


class AdapterUser:
    def __init__(
        self, db, _user_email, _password, _name, _document, _phone
    ) -> None:
        self.db = db
        self._user_email = _user_email
        self._password = _password
        self._name = _name
        self._document = _document
        self._phone = _phone

    def check_user(self):
        try:
            logger.info(f'DOCUMENT -----------------{self._document}')

            _user = check_existent_user(
                db=self.db,
                email=self._user_email,
                document=self._document,
                password=self._password,
            )
            if not _user:
                return self.user_create()
            return _user
        except Exception as e:
            logger.error('Erro ao criar usuário {e}')
            raise e

    def user_create(self):
        _sign_up = SignUp(
            name=self._name,
            mail=self._user_email,
            password=self._password,
            document=self._document,
            phone=self._phone,
        )
        _user = create_user(db=self.db, obj_in=_sign_up)
        logger.info('----------------USER----------------')
        logger.info(_user)
        return _user


def get_db():
    session_local = get_session()
    return session_local()
