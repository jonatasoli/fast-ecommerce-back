from functools import wraps
from loguru import logger
from sqlalchemy.exc import SQLAlchemyError


def database_uow():
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                async with kwargs['bootstrap'].db().begin() as inner_session:
                    result = await func(
                        *args, transaction=inner_session, **kwargs
                    )
                    await inner_session.session.commit()  # Comita a transação explicitamente
                    logger.info('Transaction committed')
            except SQLAlchemyError as e:
                logger.error(f'Error in transaction: {e}')
                inner_session.rollback()  # Realiza um rollback em caso de exceção do SQLAlchemy
                raise e  # Re-raise a exceção para que possa ser tratada em níveis superiores

            return result

        return wrapper

    return decorator
