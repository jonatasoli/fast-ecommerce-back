import psycopg2
import requests
import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean
from models.order import OrderStatusSteps
from dynaconf import settings
from loguru import logger


def get_session():
    engine = create_engine(settings.DATABASE_URL, echo=True)
    Base = declarative_base()
    Session = sessionmaker(bind=engine)
    session = Session()
    return session


def post_order_status(url):
    response = requests.post(url=url)
    return response


def process():
    session = get_session()
    result = session.query(OrderStatusSteps).filter_by(active=True, sending=False)
    result_list = [{"Order_id": row.id, "Status": row.status} for row in result]
    logger.debug(f"SETTINGS ------ {settings.API_MAIL_URL}")
    url = post_order_status(settings.API_MAIL_URL)
    return result_list


def main():
    process()


if __name__ == "__main__":
    main()
