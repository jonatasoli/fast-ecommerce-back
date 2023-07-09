from loguru import logger

from constants import DocumentType, Roles
from models.users import User
from schemas.user_schema import SignUp


def test_add_user(db_models):
    obj_in = SignUp(
        name='User Test',
        document='12345678901',
        mail='email@email.com',
        phone='11-987654321',
        password='asdasd',
    )
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
    db_models.add(db_user)
    logger.info(db_user)
    db_models.commit()

    assert db_user.id == 1
    assert db_user.role_id == 2
