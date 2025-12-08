# ruff: noqa: I001
from fastapi import APIRouter


shipping = APIRouter(
    prefix='/freight',
    tags=['freight'],
)
