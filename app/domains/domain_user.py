from sqlalchemy.orm import Session

from schemas.user_schema import SignUp, Login
from models.users import User
from constants import DocumentType, Roles


def create_user(db: Session, obj_in: SignUp):
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
    db.commit()
    db.refresh(db_user)
    return db_user


def authenticate(db: Session, user: Login):
    db_user = db.query(User).filter_by(document=user.document).first()
    if not user.password:
        raise Exception('User not password')
    if db_user and db_user.verify_password(user.password.get_secret_value()):
        pass
    else:
        raise Exception(f'User not finded {user.document}, {user.password}')
