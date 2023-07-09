from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


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
