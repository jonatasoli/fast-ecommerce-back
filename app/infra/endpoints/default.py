from fastapi import APIRouter

inventory = APIRouter(
    prefix='/inventory',
    tags=['inventory'],
)
reviews = APIRouter(
    prefix='/reviews',
    tags=['reviews'],
)

coupons = APIRouter(
    prefix='/coupons',
    tags=['coupons'],
)
campaing = APIRouter(
    prefix='/campaing',
    tags=['campaing'],
)

sales = APIRouter(
    prefix='/sales',
    tags=['sales'],
)
