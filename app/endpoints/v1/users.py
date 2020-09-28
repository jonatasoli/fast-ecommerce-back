from fastapi import Header, APIRouter, Depends
from sqlalchemy.orm import Session
from loguru import logger

from schemas.user_schema import Login, LoginResponse, SignUp, SignUpResponse
from domains import domain_user
from endpoints.deps import get_db
from dynaconf import settings

user = APIRouter()


@user.post('/login', status_code=200, response_model=LoginResponse)
async def login(
        *,
        db: Session = Depends(get_db),
        user_login: Login):
    user = domain_user.authenticate(db, user=user_login)
    message = { 'message': f'{user_login.password.get_secret_value()}'}
    return message


@user.post('/signup', status_code=201, response_model=SignUpResponse)
async def signup(
        *,
        db: Session = Depends(get_db),
        user_in: SignUp,
        ):
    user = domain_user.create_user(db,obj_in=user_in)
    if not user:
        raise Exception ('Erro kct')
    response = {
            'name': 'usuario',
            'message': 'adicionado com sucesso'
            }

    return response
