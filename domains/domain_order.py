from decimal import Decimal
import json
import math
from collections import defaultdict
from fastapi import HTTPException, status

from sqlalchemy import func, select
from loguru import logger
from sqlalchemy import Date, cast
from sqlalchemy.orm import Session

from app.infra.optimize_image import optimize_image
from app.infra.models.order import Category, ImageGallery, Order, Product
from app.infra.models.transaction import Payment, Transaction
from app.infra.models.users import Address, User
from app.entities.product import ProductCategoryInDB, ProductInDB, ProductsResponse
from schemas.order_schema import (
    CategoryInDB,
    ImageGalleryResponse,
    OrderCl,
    OrderFullResponse,
    OrderSchema,
    OrdersPaidFullResponse,
    ProductFullResponse,
    ProductSchema,
    ProductSchemaResponse,
    ProductsResponseOrder,
    TrackingFullResponse,
)


def get_product(db: Session, uri) -> ProductInDB | None:
    with db:
        query_product = select(Product).where(Product.uri == uri)
        product_db = db.scalar(query_product)
        if product_db:
            return ProductInDB.model_validate(product_db)
        return product_db


def create_product(db: Session, product_data: ProductSchema):
    db_product = Product(**product_data.model_dump(exclude={'description'}))
    db_product.description = json.dumps(product_data.description)
    with db:
        db.add(db_product)
        db.commit()
        return ProductSchemaResponse.model_validate(db_product)


def put_product(db: Session, id, product_data: ProductFullResponse):
    with db:
        product_query = select(Product).where(Product.id == id)
        product = db.execute(product_query).scalars().first()
        product = product.update(product_data)
        logger.debug(product)
        db.commit()
    return {**product_data.dict()}


def delete_product(db: Session, id):
    with db:
        db.execute(select(Product).where(Product.id == id).delete()).delete()
        db.commit()
    return {'Produto excluido'}


def upload_image(db: Session, product_id, image):
    image_path = optimize_image.optimize_image(image)
    with db:
        db_product = db.query(Product).filter(Product.id == product_id).first()
        db_product.image_path = image_path
        db.commit()
    return image_path


def upload_image_gallery(product_id, db: Session, imageGallery):
    image_path = optimize_image.optimize_image(imageGallery)
    with db:
        db_image_gallery = ImageGallery(url=image_path, product_id=product_id)
        db.add(db_image_gallery)
        db.commit()
    return image_path


def delete_image_gallery(id: int, db: Session):
    with db:
        db.execute(select(ImageGallery).where(ImageGallery.id == id)).delete()
        db.commit()
    return 'Imagem excluida'


def get_images_gallery(db: Session, uri):
    with db:
        product_id_query = select(Product).where(Product.uri == uri)
        product_id = db.execute(product_id_query).scalars().first()
        images_query = select.query(ImageGallery).where(
            ImageGallery.product_id == product_id.id,
        )
        images = db.execute(images_query).scalars().all()
        images_list = []

        for image in images:
            images_list.append(ImageGalleryResponse.from_orm(image))

        if images:
            return {'images': images_list}
        return {'images': []}


def get_showcase(db: Session):
    with db:
        showcases_query = select(Product).where(Product.showcase == True)
        showcases = db.execute(showcases_query).scalars().all()
        products = []

        for showcase in showcases:
            products.append(ProductCategoryInDB.model_validate(showcase))

        return products


def get_installments(product_id: int, *, db: Session):
    with db:
        _product_config_query = select(Product).where(
            Product.product_id == product_id,
        )
        product = db.scalar(_product_config_query)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Product not found',
            )
        _total_amount = 0
        _total_amount_fee = 0
        _installments = []

        for n in range(1, 13):
            if n <= 3:
                _installment = (product.price / n) / 100
                _installments.append(
                    {
                        'name': f'{n} x R${round(_installment, 2)}',
                        'value': f'{n}',
                    },
                )
                logger.debug(f'Parcela sem juros {_installment}')
            else:
                _total_amount_fee = int(product.price) * (1 + (0.0199 * n))
                _installment = (_total_amount_fee / n) / 100
                _installments.append(
                    {
                        'name': f'{n} x R${round(_installment, 2)}',
                        'value': f'{n}',
                    },
                )
                logger.debug(f'Parcela com juros {_installment}')

        logger.debug(f'array de parcelas {_installments}')
        return _installments


def get_product_by_id(db: Session, id):
    with db:
        product_query = select(Product).where(Product.id == id)
        product = db.execute(product_query).scalars().first()
        return ProductInDB.from_orm(product)


def get_orders_paid(db: Session, dates=None, status=None, user_id=None):
    if dates:
        logger.info(dates)
        new_date = json.loads(dates)
        date_end = {'date_end': new_date.get('date_start')}
        if 'date_end' not in new_date.keys():
            new_date.update(date_end)
    if status == 'null':
        status = None

    orders_query = (
        select(
            Transaction.order_id,
            Transaction.payment_id,
            Order.tracking_number,
            Order.order_date,
            User.id.label('user_id'),
            User.name.label('user_name'),
            User.email,
            User.phone,
            User.document,
            Transaction.affiliate,
            Payment.amount,
            Payment.gateway_id.label('id_pagarme'),
            Order.order_status.label('status'),
            Order.checked,
        )
        .join(Order, Transaction.order_id == Order.id)
        .join(Product, Transaction.product_id == Product.id)
        .join(User, Transaction.user_id == User.id)
        .join(Payment, Payment.id == Transaction.payment_id)
    )
    if dates:
        orders_query = (
            orders.where(
                Order.order_status == status,
                cast(Order.order_date, Date).between(
                    new_date.get('date_start'),
                    new_date.get('date_end'),
                ),
            )
            .distinct()
            .all()
        )
    if user_id:
        user_query = select(User).where(User.document == str(user_id))
        user = db.execute(user_query).scalars().first()

        orders_query = (
            orders.where(Order.customer_id == user.id).distinct().all()
        )
    order_list = []
    product_list = []
    orders = db.execute(orders_query).scalars().all()
    for order in orders:
        address_query = select(
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
        ).where(
            Address.category == 'shipping',
            Address.user_id == order.user_id,
        )
        address = db.execute(address_query).scalars().first()

        affiliate = None
        if order.affiliate is not None:
            affiliates_query = select(User.name).where(
                order.affiliate == User.uuid,
                Transaction.payment_id == order.payment_id,
            )
            affiliates = db.execute(affiliates_query).scalars().all()
            for affil in affiliates:
                affiliate = affil

        products_query = (
            select(
                Product.name.label('product_name'),
                Product.image_path,
                Transaction.amount.label('price'),
                Transaction.qty,
                Transaction.payment_id,
                Transaction.order_id,
            )
            .join(Product, Transaction.product_id == Product.id)
            .where(Transaction.payment_id == order.payment_id)
        )
        products = db.execute(products_query).scalars().all()
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
            id_pagarme=order.id_pagarme,
            status=order.status,
            order_id=order.order_id,
            tracking_number=order.tracking_number,
            order_date=order.order_date.date().strftime('%d-%m-%y'),
            user_name=order.user_name,
            email=order.email,
            phone=order.phone,
            document=order.document,
            type_address=address.type_address,
            category=address.category,
            country=address.country,
            city=address.city,
            state=address.state,
            neighborhood=address.neighborhood,
            street=address.street,
            street_number=address.street_number,
            address_complement=address.address_complement,
            zipcode=address.zipcode,
            user_affiliate=affiliate,
            amount=order.amount,
            checked=order.checked,
            products=prods,
        )

        order_list.append(OrdersPaidFullResponse.from_orm(orders_all))
    if orders:
        return {'orders': order_list}
    return {'orders': []}


def get_order(db: Session, id):
    with db:
        users_query = (
            select(User)
            .join(Order, Order.customer_id == User.id)
            .where(Order.id == id)
        )
        users = db.execute(users_query).scalars().all()
        orders_query = (
            select(Order)
            .join(User, Order.customer_id == User.id)
            .where(Order.id == id)
        )
        orders = db.execute(orders_query).scalars().all()
        for user in users:
            orderObject = {'name': user.name, 'order': []}
            for order in orders:
                order = {
                    'id': order.id,
                    'customer_id': order.customer_id,
                    'order_date': order.order_date,
                    'tracking_number': order.tracking_number,
                    'payment_id': order.payment_id,
                }
                orderObject['order'].append(order)
                return orderObject
        return None


def get_order_users(db: Session, id):
    orderObject = None
    with db:
        users_query = (
            select(User)
            .join(Order, Order.customer_id == User.id)
            .where(User.id == id)
        )
        users = db.execute(users_query).scalars().all()
        orders_query = (
            select(Order)
            .join(User, Order.customer_id == User.id)
            .where(User.id == id)
        )
        orders = db.execute(orders_query).scalars().all()
        for user in users:
            orderObject = {'name': user.name, 'orders': []}
            for order in orders:
                order = {
                    'id': order.id,
                    'customer_id': order.customer_id,
                    'order_date': order.order_date,
                    'tracking_number': order.tracking_number,
                    'payment_id': order.payment_id,
                }
                orderObject['orders'].append(order)
            return orderObject
        return None


def put_order(db: Session, order_data: OrderFullResponse, id):
    with db:
        order_query = select(Order).where(Order.id == id)
        db.execute(order_query).scalars().first()
        order_data.dict()
        db.commit()
        return {**order_data.dict()}


def put_trancking_number(db: Session, data: TrackingFullResponse, id):
    order = None
    with db:
        order = select(Order).where(Order.id == id)
        order = order.update(data)
        db.commit()
    return {**data.dict()}


def checked_order(db: Session, id, check):
    db_order = None
    with db:
        db_order_query = select(Order).where(Order.id == id)
        db_order = db.execute(db_order_query).scalars().first()
        db_order.checked = check
        db.commit()
    return db_order


def create_order(db: Session, order_data: OrderSchema):
    db_order = Order(**order_data.dict())
    with db:
        db.add(db_order)
        db.commit()
        db.refresh(db_order)
    return db_order


def get_category(db: Session):
    categorys = None
    with db:
        categorys_query = select(Category)
        categorys = db.execute(categorys_query).scalars().all()

    category_list = []

    for category in categorys:
        category_list.append(CategoryInDB.from_orm(category))
    return {'category': category_list}


class NotFoundCategoryException(Exception):
    """Not Found Category Exception."""
    ...

def get_products_category(*, offset: int, page: int, path: str, db: Session) -> ProductsResponse:
    products = None
    products_category = []
    with db:
        category_query = select(Category).where(Category.path == path)
        category = db.scalar(category_query)

        if not category:
            raise NotFoundCategoryException()

        logger.info(category.path, category.category_id)

        products_query = (
            select(Product)
            .where(
                Product.category_id == category.category_id,
            )
        )
        total_records = db.scalar(select(func.count(Product.product_id)).where(Product.category_id == category.category_id))
        if page > 1:
            products_query = products_query.offset((page - 1) * offset)
        products_query = products_query.limit(offset)

        products = db.scalars(products_query)

        for product in products:
            products_category.append(ProductCategoryInDB.model_validate(product))

    return ProductsResponse(
        total_records=total_records if total_records else 0,
        total_pages= math.ceil(total_records / offset) if total_records else 1,
        page=page,
        offset=offset,
        products=products_category
    )


def get_product_all(offset: int, page: int, db: Session) -> ProductsResponse:
    products = None
    total_records = 0
    with db:
        products = select(Product)
        total_records = db.scalar(select(func.count(Product.product_id)))
        if page > 1:
            products = products.offset((page - 1) * offset)
        products = products.limit(offset)

        products = db.scalars(products).all()
    products_list = []

    for product in products:
        products_list.append(ProductCategoryInDB.model_validate(product))

    return ProductsResponse(
        total_records=total_records if total_records else 0,
        total_pages= math.ceil(total_records / offset) if total_records else 1,
        page=page,
        offset=offset,
        products=products_list
    )


def get_latest_products(offset: int, page: int, db: Session) -> ProductsResponse:
    products = None
    with db:
        products = select(Product)
        total_records = db.scalar(select(func.count(Product.product_id)))
        if page > 1:
            products = products.offset((page - 1) * offset)
        products = products.limit(offset)
        products = products.order_by(Product.product_id.desc())

        products = db.scalars(products).all()
    products_list = []

    for product in products:
        products_list.append(ProductCategoryInDB.model_validate(product))

    return ProductsResponse(
        total_records=total_records if total_records else 0,
        total_pages= math.ceil(total_records / offset) if total_records else 1,
        page=page,
        offset=offset,
        products=products_list
    )


def get_featured_products(offset: int, page: int, db: Session) -> ProductsResponse:
    products = None
    with db:
        products = select(Product).where(Product.feature == True)
        total_records = db.scalar(select(func.count(Product.product_id)))
        if page > 1:
            products = products.offset((page - 1) * offset)
        products = products.limit(offset)

        products = db.scalars(products).all()
    products_list = []

    for product in products:
        products_list.append(ProductCategoryInDB.model_validate(product))

    return ProductsResponse(
        total_records=total_records if total_records else 0,
        total_pages= math.ceil(total_records / offset) if total_records else 1,
        page=page,
        offset=offset,
        products=products_list
    )


def search_products(search:str, offset: int, page: int,  db: Session):
    products = None
    with db:
        products = select(Product).where(Product.name.ilike(f"%{search}%"))
        total_records = db.scalar(select(func.count(Product.product_id)).where(Product.name.ilike(f"%{search}%")))
        if page > 1:
            products = products.offset((page - 1) * offset)
        products = products.limit(offset)
        products = db.scalars(products).all()
    products_list = []

    for product in products:
        products_list.append(ProductCategoryInDB.model_validate(product))

    return ProductsResponse(
        total_records=total_records if total_records else 0,
        total_pages= math.ceil(total_records / offset) if total_records else 1,
        page=page,
        offset=offset,
        products=products_list
    )
