from fastapi import Header, APIRouter, Depends
from sqlalchemy.orm import Session
from loguru import logger
from datetime import datetime, timedelta
from fastapi.security import OAuth2PasswordRequestForm

from schemas.user_schema import Login, LoginResponse, SignUp, SignUpResponse,\
        Token
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


fake_users_db = {
    "johndoe": {
        "username": "johndoe",
        "full_name": "John Doe",
        "email": "johndoe@example.com",
        "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
        "disabled": False,
    }
}

@user.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = domain_user.authenticate_user(fake_users_db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = domain_user.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


