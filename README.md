# Fast Ecommerce
## ApiRest in development
[![Updates](https://pyup.io/repos/github/jonatasoli/fast-ecommerce/shield.svg)](https://pyup.io/repos/github/jonatasoli/fast-ecommerce/)
[![Python 3](https://pyup.io/repos/github/jonatasoli/fast-ecommerce/python-3-shield.svg)](https://pyup.io/repos/github/jonatasoli/fast-ecommerce/)

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
uvicorn main:app --reload --host 0.0.0.0 --port 7777
````

## Tests

* Create postgres database "test"
* Enter in app directory
* Run tests
````
python -m pytest
````


## Technologies
+ [PostgreSql](https://www.postgresql.org/)
+ [FastApi](https://fastapi.tiangolo.com/)
+ [DynaConf](https://www.dynaconf.com/)

