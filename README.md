# Fast Ecommerce
ApiRest in development

<p>
 <a href="#pre-requirements">Pre-requirements</a> •
 <a href="#install">Install</a> • 
 <a href="#technologies">Technologies</a> 
</p

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

## Technologies
+ [PostgreSql](https://www.postgresql.org/)
+ [FastApi](https://fastapi.tiangolo.com/)
+ [DynaConf](https://www.dynaconf.com/)

