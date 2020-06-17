import pytest


def test_signup(test_client, db) -> None:
    signup_data = {
            "name": "Jonatas Luiz de Oliveira",
            "mail": "contato@jonatasoliveira.me",
            "password": "asdasd",
            "document": "12345678910",
            "phone": "11912345678"
            }
    r = test_client.post("/signup", json=signup_data)

    response = r.json()
    assert r.status_code == 201
    assert response == { 
            'name': 'usuario',
            'message': 'adicionado com sucesso'
            }

    
def test_read_main(test_client):
    response = test_client.get("/")
    assert response.status_code == 200
    assert response.json() == {"Real": "Python"}


def test_login(test_client) -> None:
    login_data = {
        "document": "12345678910",
        "password": "asdasd"
    }
    r = test_client.post("/login", json=login_data)
    response = r.json()
    assert r.status_code == 200
    assert response == {'message': 'asdasd'}


def test_invalid_signup(test_client) -> None:
    signup_data = {
            "name": "Jonatas Luiz de Oliveira",
            "mail": "contato@jonatasoliveira.me",
            "password": "asdasd",
            }
    r = test_client.post("/signup", json=signup_data)

    response = r.json()
    assert r.status_code == 422
# def test_use_access_token(
#     client: TestClient, superuser_token_headers: Dict[str, str]
# ) -> None:
#     r = client.post(
#         f"{settings.API_V1_STR}/login/test-token", headers=superuser_token_headers,
#     )
#     result = r.json()
#     assert r.status_code == 200
#     assert "email" in result
