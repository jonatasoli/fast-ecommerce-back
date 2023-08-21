from propan.brokers.rabbit import RabbitQueue
from propan.fastapi import RabbitRouter
from pydantic import BaseModel

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger


task_cart_router = RabbitRouter("amqp://guest:guest@localhost:5672//")

class Incoming(BaseModel):
    username: str

def call():
    return True

@task_cart_router.event(RabbitQueue("test"))
async def hello(m: Incoming, d = Depends(call)):
    logger.info(f" log test {m.username}")
    return m.username

app = FastAPI(lifespan=task_cart_router.lifespan_context)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

@app.post('/test/{username}')
async def test(username: str):
    task_response = await task_cart_router.broker.publish({"username": username}, queue=RabbitQueue('test'), callback=True)
    logger.info(f"The task response is {task_response}")

    return { "response": f"Hiiii, {username}! {str(task_response)}" }

app.include_router(task_cart_router)
