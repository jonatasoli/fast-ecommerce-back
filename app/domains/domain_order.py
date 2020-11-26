from sqlalchemy.orm import Session
from loguru import logger

from schemas.order_schema import ProductSchema, OrderSchema, OrderFullResponse, ProductInDB, ListProducts

from models.order import Product, Order, OrderItems
from models.users import User

def get_product(db : Session, uri):
    return db.query(Product).filter(Product.uri == uri).first()


def create_product(db: Session, product_data: ProductSchema):
    db_product = Product(**product_data.dict())
    db.add(db_product)
    db.commit()
    return db_product


def get_showcase(db:Session):
    showcases = db.query(Product).all()
    products = []

    for showcase in showcases:
        products.append(ProductInDB.from_orm(showcase))
    
    if showcases:
        return { "products": products}
    return { "products": []}


def get_installments(db: Session, cart):
    _cart = cart.dict()
    _product_id = _cart['cart'][0]['product_id']
    _product_config = db.query(Product).filter_by(id=int(_product_id)).first()
    _total_amount = 0
    _installments = []

    for item in _cart['cart']:
        _total_amount += (item['amount'] * item['qty'])

    for n in range(1,13):
        _installment = (_total_amount/n)/100
        _installments.append({"name": f"{n} x R${_installment}", "value": f"{n}"})


    return _installments
    # _config_installments = db.query(CreditCardFeeConfig)\
    #     .filter_by(id=_product_config.installments_config)\
    #     .first()
    # if _installments > 12:
    #     raise Exception("O número máximo de parcelas é 12") 
    # elif _installments >= _config_installments.min_installment_with_fee:
    #     _total_amount = _total_amount * ((1+_config_installments.fee) ** _installments)


def get_product_by_id(db: Session, id):
    product = db.query(Product).filter_by(id=id).first()
    return ProductInDB.from_orm(product)


def get_order(db: Session, id):
    users = db.query(User).join(Order, Order.customer_id == User.id).filter(Order.id == id)
    orders = db.query(Order).join(User, Order.customer_id == User.id).filter(Order.id == id)
    for user in users:
        orderObject= {
            "name": user.name,
            "order": []}
        for order in orders:
            order = {
                "id": order.id,
                "customer_id": order.customer_id,
                "order_date": order.order_date,
                "tracking_number": order.tracking_number,
                "payment_id": order.payment_id}
            orderObject['order'].append(order)
            return orderObject
    

def get_order_users(db: Session, id):
    users = db.query(User).join(Order, Order.customer_id == User.id).filter(User.id == id)
    orders = db.query(Order).join(User, Order.customer_id == User.id).filter(User.id == id)
    for user in users:
        orderObject= {
            "name": user.name,
            "orders": []}
        for order in orders:
            order = {
                "id": order.id,
                "customer_id": order.customer_id,
                "order_date": order.order_date,
                "tracking_number": order.tracking_number,
                "payment_id": order.payment_id}
            orderObject['orders'].append(order)
            return orderObject


def put_order(db: Session, order_data: OrderFullResponse ,id):
    order= db.query(Order).filter(Order.id == id)
    order= order.update(order_data)
    return ({**order_data.dict()})
  
    
def create_order(db: Session, order_data: OrderSchema):
    db_order = Order(**order_data.dict())
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    return db_order
