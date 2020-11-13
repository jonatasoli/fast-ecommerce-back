from fastapi import Header, APIRouter, Depends
from sqlalchemy.orm import Session
from loguru import logger
from datetime import datetime, timedelta
from fastapi.security import OAuth2PasswordRequestForm

from schemas.user_schema import SignUp, SignUpResponse,\
        Token
from domains import domain_user
from endpoints.deps import get_db
from dynaconf import settings

user = APIRouter()


@user.post('/signup', status_code=201, response_model=SignUpResponse)
async def signup(
        *,
        db: Session = Depends(get_db),
        user_in: SignUp,
        ):
    user = domain_user.create_user(db,obj_in=user_in)
    if not user:
        raise Exception ('Não foi possível criar o usuário')
    response = {
            'name': 'usuario',
            'message': 'adicionado com sucesso'
            }

    return response


@user.post("/token", response_model=Token)
async def login_for_access_token(
        form_data: OAuth2PasswordRequestForm = Depends(),
        db: Session = Depends(get_db)
        ):
    user = domain_user.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = domain_user.create_access_token(
        data={"sub": user.document}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


