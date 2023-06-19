# Fast Ecommerce
## ApiRest in development

 [Pre-requirements](#pre-requirements)
 [Install](#install) 
 [Technologies](#technologies) 

## Pre-requirements
+ PostgreSQL
+ Repository clone
```
git clone https://github.com/jonatasoli/fast-ecommerce
```
```
cd fast-ecommerce
cd app
```

+ Virtualenv
```
 pip install virtualenv
```
Create Virtualenv
````
virtualenv (namevirtualenv)
````
Activate virtualenv
Windows 
````
(namevirtualenv)\Scripts\activate.bat
````
Linux ou Mac
````
source (namevirtualenv)/bin/activate
````
Install requiriments
````
pip install -r requirements.txt
````

## Install
````
alembic upgrade head
````
````
uvicorn main:app --reload --host 0.0.0.0 --port 8001
````

## Tests

* Create postgres database "test"
* Enter in app directory
* Run tests
````
python -m pytest
````

## Getting Started

* Create Roles in database
|id|status|role|
|1|active|ADMIN|
|2|active|USER|
|3|active|AFFIALIATE|

* Create user with route -> /user/signup
* Enter in database and change role_id from 2 to 1

* Create credit card config with route -> /create-config
>[!info]
> Credit card config need tax installment fee, min and max installments

* Create product with route -> create_product
suggest test product
```json
    product = {
        'description': 'Test Product',
        'direct_sales': None,
        'installments_config': 1,
        'name': 'Test',
        'price': 10000,
        'upsell': None,
        'uri': '/test',
        'image_path': 'https://i.pinimg.com/originals/e4/34/2a/e4342a4e0e968344b75cf50cf1936c09.jpg',
        'quantity': 100,
        'discount': 100,
        'category_id': 1,
        'installments_list': [
            {'name': '1', 'value': 'R$100,00'},
            {'name': '2', 'value': 'R$50,00'},
            {'name': '3', 'value': 'R$33,00'},
            {'name': '4', 'value': 'R$25,00'},
            {'name': '5', 'value': 'R$20,00'},
        ],
    }
```

## Technologies
+ [PostgreSql](https://www.postgresql.org/)
+ [FastApi](https://fastapi.tiangolo.com/)
+ [DynaConf](https://www.dynaconf.com/)

