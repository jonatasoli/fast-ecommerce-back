from datetime import timedelta
from typing import List, Optional

from dynaconf import settings
from fastapi import APIRouter, Depends, Header, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from loguru import logger
from sqlalchemy.orm import Session

from domains import domain_user
from domains.domain_user import check_token
from endpoints.deps import get_db
from schemas.user_schema import (SignUp, SignUpResponse, Token,
                                 UserResponseResetPassword)

user = APIRouter()


oauth2_scheme = OAuth2PasswordBearer(tokenUrl='access_token')


@user.post('/signup', status_code=201, response_model=SignUpResponse)
async def signup(
    *,
    db: Session = Depends(get_db),
    user_in: SignUp,
):
    user = domain_user.create_user(db, obj_in=user_in)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Não foi possível criar o usuário',
        )
    response = {'name': 'usuario', 'message': 'adicionado com sucesso'}

    return response


@user.get('/dashboard', status_code=200)
@check_token
def dashboard(
    *,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
):
    user = domain_user.get_current_user(token)
    role = domain_user.get_role_user(db, user.role_id)
    response = {'role': role}

    return response


@user.post('/token', response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    user = domain_user.authenticate_user(
        db, form_data.username, form_data.password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Incorrect username or password',
            headers={'WWW-Authenticate': 'Bearer'},
        )
    access_token_expires = timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    access_token = domain_user.create_access_token(
        data={'sub': user.document}, expires_delta=access_token_expires
    )
    role = domain_user.get_role_user(db, user.role_id)

    response = {
        'access_token': access_token,
        'token_type': 'bearer',
        'role': role,
    }
    return response


@user.get('/user/{document}', status_code=200)
async def get_user(document: str, db: Session = Depends(get_db)):
    return domain_user.get_user_login(db, document)


@user.post('/request-reset-password', status_code=200)
async def request_reset_password(document: str, db: Session = Depends(get_db)):
    return domain_user.save_token_reset_password(db, document)


@user.put('/reset-password', status_code=200)
async def reset_password(
    response_model: UserResponseResetPassword, db: Session = Depends(get_db)
):
    return domain_user.reset_password(db, data=response_model)
