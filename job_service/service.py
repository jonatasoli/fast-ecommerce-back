import httpx
from dynaconf import settings
from loguru import logger
from sqlalchemy import (
    create_engine,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.infra.models import OrderStatusStepsDB


def get_session():
    engine = create_engine(settings.DATABASE_URL, echo=True)
    declarative_base()
    Session = sessionmaker(bind=engine)
    return Session()


def post_order_status(url):
    return httpx.post(url=url)


def process():
    session = get_session()
    result = session.query(OrderStatusStepsDB).filter_by(
        active=True,
        sending=False,
    )
    result_list = [
        {'Order_id': row.id, 'Status': row.status} for row in result
    ]
    logger.debug(f'SETTINGS ------ {settings.API_MAIL_URL}')
    post_order_status(settings.API_MAIL_URL)
    return result_list


def main():
    process()


if __name__ == '__main__':
    main()
