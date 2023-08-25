from app.cart.uow import get_session


def get_db() -> None:
    """Get db."""
    sessionlocal = get_session()
    db = sessionlocal()
    try:
        yield db
    finally:
        db.close()
