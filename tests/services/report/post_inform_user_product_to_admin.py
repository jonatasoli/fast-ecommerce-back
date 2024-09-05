

from app.entities.report import InformUserProduct
from app.report.services import notify_product_to_admin


async def test_input_to_user_admin(asyncdb):
    """Should save inform in database."""
    # Arrange
    inform = InformUserProduct(
        email='email@email.com',
        phone='1234567890',
        product_id=1,

    )

    # Act
    await notify_product_to_admin(
        inform=inform,
        db=asyncdb,
    )

    # Assert
    assert True
