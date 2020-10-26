from models.users import User


def test_add_user(db):
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
    logger.info(db_user)
    db.commit()
    db.refresh(db_user)
    
    assert db_user.id == 1
    assert db_user.role == "USER"
