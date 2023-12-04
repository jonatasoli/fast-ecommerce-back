from app.infra.bootstrap.task_bootstrap import bootstrap
from app.cart.tasks import checkout


def test_checkout_task(mocker):
    # Arrange
    mock_bootstrap = bootstrap()
    mock_cache = mocker.patch.object(
        mock_bootstrap.cache, 'get', return_value={'key': 'value'},
    )
    mock_bootstrap.cache = mock_cache

    # Call the task with mocked dependencies
    result = checkout(
        cart_uuid='test_cart_uuid',
        payment_intent='test_payment_intent',
        bootstrap=mock_bootstrap,
    )

    # Assertions or checks for the expected behavior
    assert result is None  # Since the task returns None

    # You can also assert if the methods on mock objects were called as expected
    mock_cache.get.assert_called_once_with('test_cart_uuid')
