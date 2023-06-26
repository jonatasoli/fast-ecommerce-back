from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware

from config import settings

# from todo.api.endpoints import todo_router

catalog = FastAPI()


origins = [
    '*',
]

catalog.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

# catalog.include_router(
#     catalog_router,
#     responses={status.HTTP_404_NOT_FOUND: {'description': 'Not found'}},
# )
