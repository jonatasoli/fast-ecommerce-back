from celery import Celery

from config import settings


def create_worker() -> Celery:
    """Must create a celery worker."""
    return Celery(
        'tasks',
        broker=settings.BROKER_URL,
        backend=settings.RESULT_BACKEND,
    )


celery = create_worker()
