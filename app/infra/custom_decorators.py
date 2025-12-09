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
                        *args,
                        transaction=inner_session,
                        **kwargs,
                    )
                    await (
                        inner_session.session.commit()
                    )
                    logger.info('Transaction committed')
            except SQLAlchemyError as e:
                logger.error(f'Error in transaction: {e}')
                inner_session.rollback()
                raise

            return result

        return wrapper

    return decorator
