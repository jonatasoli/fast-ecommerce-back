from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import literal_column, cast, Date, between
from sqlalchemy.sql import func, compiler
from loguru import logger
from ext import optimize_image
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
    TrackingFullResponse,
    ImageGalleryResponse
)

from models.order import Product, Order, OrderItems, Category, ImageGallery
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


def upload_image(db: Session, product_id, image):
    image_path = optimize_image.optimize_image(image)
    db_product = db.query(Product).filter(Product.id == product_id).first()
    db_product.image_path = image_path
    db.commit()
    return image_path


def upload_image_gallery(product_id, db: Session, imageGallery):
    image_path = optimize_image.optimize_image(imageGallery)
    db_image_gallery = ImageGallery(url= image_path, product_id= product_id)
    db.add(db_image_gallery)
    db.commit()
    return image_path


def delete_image_gallery(id: int, db: Session):
    db.query(ImageGallery).filter(ImageGallery.id == id).delete()
    db.commit()
    return "Imagem excluida"


def get_images_gallery(db: Session, uri):
    product_id = db.query(Product).filter(Product.uri == uri).first()
    images = db.query(ImageGallery).filter(ImageGallery.product_id == product_id.id).all()
    images_list = []

    for image in images:
        images_list.append(ImageGalleryResponse.from_orm(image))
    
    if images:
        return {"images": images_list}
    return {"images": []}



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


def get_orders_paid(db: Session, dates, status):
    new_date = json.loads(dates)
    date_end = {'date_end': new_date.get('date_start')}
    table_date = Order.last_updated
    if 'date_end' not in new_date.keys():
        new_date.update(date_end)
    if status == "null":
        status = None
        table_date = Order.order_date

    orders = db.query(
        Transaction.order_id,
        Transaction.payment_id, 
        Order.tracking_number,
        Order.order_date,
        User.id.label("user_id"),
        User.name.label('user_name'),
        User.email,
        User.phone,
        User.document,
        Transaction.affiliate,
        Payment.amount,
        Payment.gateway_id.label('id_pagarme'),
        Order.order_status.label('status')
        )\
    .join(Order, Transaction.order_id == Order.id)\
    .join(Product, Transaction.product_id == Product.id)\
    .join(User, Transaction.user_id == User.id)\
    .join(Payment, Payment.id == Transaction.payment_id)\
        .filter(
            Order.order_status == status,
            cast(Order.order_date, Date).between(
                new_date.get('date_start'), new_date.get('date_end')
            )).distinct().all()
    print(status)
    order_list = []
    product_list = []
    print(orders)
    for order in orders:
        address = db.query(
            Address.user_id,
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
        ).filter(
            Address.category == 'shipping',
            Address.user_id == order.user_id).first()
        

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
            Transaction.amount.label('price'),
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
            order_date= order.order_date.date().strftime('%d-%m-%y'),
            user_name= order.user_name,
            email = order.email,
            phone = order.phone,
            document= order.document,
            type_address= address.type_address,
            category= address.category,
            country = address.country,
            city = address.city,
            state= address.state,
            neighborhood= address.neighborhood,
            street= address.street,
            street_number= address.street_number,
            address_complement= address.address_complement,
            zipcode= address.zipcode,
            user_affiliate= affiliate,
            amount= order.amount,
            products= prods)

        order_list.append(OrdersPaidFullResponse.from_orm(orders_all))
    print(new_date)    
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



def get_products_category(db: Session, path):
    category = db.query(Category).filter(Category.path == path).first()
    print(category.path, category.id)
    products = db.query(Product).filter(Product.showcase == True, 
    Product.category_id == category.id).all()
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
