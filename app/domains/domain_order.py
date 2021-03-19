from sqlalchemy.orm import Session
from sqlalchemy import case, literal_column, cast, Date, true, false
from sqlalchemy.sql import func, compiler
from loguru import logger
from collections import defaultdict

from schemas.order_schema import (
    ProductSchema,
    OrderSchema,
    OrderFullResponse,
    ProductInDB,
    ListProducts,
    CategorySchema,
    CategoryInDB,
    ProductFullResponse,
    OrdersPaidFullResponse,
    ProductsResponseOrder,
    OrderCl,
    TrackingFullResponse
)

from models.order import Product, Order, OrderItems, Category
from models.transaction import Payment, Transaction
from models.users import User, Address
from loguru import logger
import requests
import json


def get_product(db: Session, uri):
    return db.query(Product).filter(Product.uri == uri).first()


def create_product(db: Session, product_data: ProductSchema):
    db_product = Product(**product_data.dict())
    db.add(db_product)
    db.commit()
    return db_product


def put_product(db: Session, id, product_data: ProductFullResponse):
    product = db.query(Product).filter(Product.id == id)
    product = product.update(product_data)
    logger.debug(product)
    db.commit()
    return {**product_data.dict()}


def delete_product(db: Session, id):
    db.query(Product).filter(Product.id == id).delete()
    db.commit()
    return {"Produto excluido"}


def get_showcase(db: Session):
    showcases = db.query(Product).filter_by(showcase=True).all()
    products = []

    for showcase in showcases:
        products.append(ProductInDB.from_orm(showcase))

    if showcases:
        return {"products": products}
    return {"products": []}


def get_installments(db: Session, cart):
    _cart = cart.dict()
    _product_id = _cart["cart"][0]["product_id"]
    _product_config = db.query(Product).filter_by(id=int(_product_id)).first()
    _total_amount = 0
    _total_amount_fee = 0
    _installments = []

    for item in _cart["cart"]:
        _total_amount += item["amount"] * item["qty"]

    logger.debug(f"Total da soma {_total_amount}")
    for n in range(1, 13):
        if n <= 3:
            _installment = (_total_amount / n) / 100
            _installments.append(
                {"name": f"{n} x R${round(_installment, 2)}", "value": f"{n}"}
            )
            logger.debug(f"Parcela sem juros {_installment}")
        else:
            _total_amount_fee = _total_amount * (1 + 0.0199) ** n
            _installment = (_total_amount_fee / n) / 100
            _installments.append(
                {"name": f"{n} x R${round(_installment, 2)}", "value": f"{n}"}
            )
            logger.debug(f"Parcela com juros {_installment}")

    logger.debug(f"array de parcelas {_installments}")
    return _installments


def get_product_by_id(db: Session, id):
    product = db.query(Product).filter_by(id=id).first()
    return ProductInDB.from_orm(product)


def get_orders_paid(db: Session, date_now):

    orders = db.query(
        Transaction.order_id,
        Transaction.payment_id, 
        Order.tracking_number,
        User.name.label('user_name'),
        User.document,
        Address.type_address,
        Address.category,
        Address.country,
        Address.city,
        Address.state,
        Address.neighborhood,
        Address.street,
        Address.street_number,
        Address.address_complement,
        Address.zipcode,
        Transaction.affiliate,
        Payment.amount,
        Payment.gateway_id.label('id_pagarme'),
        Order.order_status.label('status')
        )\
    .join(Order, Transaction.order_id == Order.id)\
    .join(Product, Transaction.product_id == Product.id)\
    .join(User, Transaction.user_id == User.id)\
    .join(Address, User.id == Address.user_id)\
    .join(Payment, Payment.id == Transaction.payment_id)\
        .filter(
            Order.order_status == 'paid',
            User.id == Address.user_id,
            Address.category == 'shipping',
            cast(Order.last_updated, Date) == date_now ).distinct().all()

    order_list = []
    product_list = []

    for order in orders:
        affiliate = None
        if order.affiliate != None:
            affiliates = db.query(User.name)\
                .filter(
                    order.affiliate == User.uuid, 
                    Transaction.payment_id == order.payment_id).first()
            for affil in affiliates:
                affiliate = affil
        
        products = db.query(
            Product.name.label('product_name'),
            Product.price,
            Transaction.qty,
            Transaction.payment_id,
            Transaction.order_id
            )\
            .join(Product, Transaction.product_id == Product.id)\
            .filter(Transaction.payment_id == order.payment_id)
        for product in products:
            product_all = ProductsResponseOrder.from_orm(product)
            product_list.append(product_all)
        
        product_grouped = defaultdict(list)
       

        for item in product_list:
            if item.payment_id == order.payment_id:
                product_grouped[item.payment_id].append(item)
        prods = []
        prods = product_grouped.pop(item.payment_id)
        
        orders_all = OrderCl(
            payment_id=order.payment_id,
            id_pagarme = order.id_pagarme,
            status = order.status,
            order_id = order.order_id,
            tracking_number= order.tracking_number,
            user_name= order.user_name,
            document= order.document,
            type_address= order.type_address,
            category= order.category,
            country = order.country,
            city = order.city,
            state= order.state,
            neighborhood= order.neighborhood,
            street= order.street,
            street_number= order.street_number,
            address_complement= order.address_complement,
            zipcode= order.zipcode,
            user_affiliate= affiliate,
            amount= order.amount,
            products= prods)

        order_list.append(OrdersPaidFullResponse.from_orm(orders_all))
            
    if orders:
        return {"orders":order_list}
    return {"orders": []}
    
    

def get_order(db: Session, id):
    users = (
        db.query(User).join(Order, Order.customer_id == User.id).filter(Order.id == id)
    )
    orders = (
        db.query(Order).join(User, Order.customer_id == User.id).filter(Order.id == id)
    )
    for user in users:
        orderObject = {"name": user.name, "order": []}
        for order in orders:
            order = {
                "id": order.id,
                "customer_id": order.customer_id,
                "order_date": order.order_date,
                "tracking_number": order.tracking_number,
                "payment_id": order.payment_id,
            }
            orderObject["order"].append(order)
            return orderObject


def get_order_users(db: Session, id):
    users = (
        db.query(User).join(Order, Order.customer_id == User.id).filter(User.id == id)
    )
    orders = (
        db.query(Order).join(User, Order.customer_id == User.id).filter(User.id == id)
    )
    for user in users:
        orderObject = {"name": user.name, "orders": []}
        for order in orders:
            order = {
                "id": order.id,
                "customer_id": order.customer_id,
                "order_date": order.order_date,
                "tracking_number": order.tracking_number,
                "payment_id": order.payment_id,
            }
            orderObject["orders"].append(order)
            return orderObject


def put_order(db: Session, order_data: OrderFullResponse, id):
    order = db.query(Order).filter(Order.id == id)
    order = order.update(order_data)
    return {**order_data.dict()}

def put_trancking_number(db: Session, data: TrackingFullResponse, id):
    order = db.query(Order).filter(Order.id == id)
    order = order.update(data)
    db.commit()
    return {**data.dict()}

def create_order(db: Session, order_data: OrderSchema):
    db_order = Order(**order_data.dict())
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    return db_order


def get_category(db: Session):
    categorys = db.query(Category).all()
    category_list = []

    for category in categorys:
        category_list.append(CategoryInDB.from_orm(category))
    return {"category": category_list}



def get_products_category(db: Session, id):
    products = db.query(Product).filter_by(active=True, category_id=id).all()
    products_category = []

    for product in products:
        products_category.append(product)

    if products:
        return {"product": products_category}
    return {"product": []}


def get_product_all(db: Session):
    products = db.query(Product).all()
    products_list = []

    for product in products:
        products_list.append(ProductInDB.from_orm(product))

    if products:
        return {"products": products_list}
    return {"products": []}
