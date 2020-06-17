from fastapi import FastAPI
from endpoints.v1.users import user

app = FastAPI()

app.include_router(user)

@app.get('/')
async def index():
    return {"Real": "Python"}


