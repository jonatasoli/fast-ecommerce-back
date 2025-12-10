import pytest
from io import BytesIO

URL = '/product'


@pytest.mark.asyncio
async def test_add_new_image_file_in_product(
    async_client,
    mocker,
) -> None:
    # Setup
    product_id = 1
    new_image_path = 'https://cdn.site.com/new_image_path'

    mocker.patch('app.product.services.upload_image', return_value=new_image_path)

    # Act
    dummy_image = BytesIO(b'fake image content')
    files = {'image': ('test.png', dummy_image, 'image/png')}

    response = await async_client.post(
        f'{URL}/upload-image/{product_id}',
        files=files,
    )

    assert response.status_code == 200
    assert response.json() == new_image_path
