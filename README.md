[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=jonatasoli_fast-ecommerce-back&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=jonatasoli_fast-ecommerce-back)
[![Coverage](https://sonarcloud.io/api/project_badges/measure?project=jonatasoli_fast-ecommerce-back&metric=coverage)](https://sonarcloud.io/summary/new_code?id=jonatasoli_fast-ecommerce-back)
# Capicart Backend
## ApiRest in development

 [Pre-requirements](#pre-requirements)
 [Install](#install)
 [Technologies](#technologies)

## Pre-requirements
+ Dcoker and docker-compose
+ Install [uv](https://docs.astral.sh/uv/getting-started/installation/)
```bash
icurl -LsSf https://astral.sh/uv/install.sh | sh
```
+ Repository clone
```bash
git clone https://github.com/jonatasoli/fast-ecommerce-back.git
```
```bash
cd fast-ecommerce-back
cd app
```
+ Start docker-compose file in [main project](https://github.com/jonatasoli/capi-cart)
```bash
docker-compose up -d
```

+ Virtualenv with uv
```bash
uv python install
```
Create Virtualenv and install requirements
````bash
uv sync
````

## Install
````bash
alembic upgrade head
or
make upgrade
````
Run project
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8001
or
make run
````

## Tests

* Create postgres database "test"
* Enter in app directory
* Run tests
````
make test
````


## Domains

* User: Handles all user management operations, such as user registration, login, and profile management.
* Direct Sales: Manages operations related to selling a product directly, bypassing any intermediary.
* Payment: Handles all payment-related operations, including processing payments through various methods such as credit cards, PIX, boleto, and installment plans.
* Freight: Responsible for managing operations related to shipping, delivery, and logistics.
* Order: Manages operations related to processing and fulfilling customer orders, including order creation, tracking, and status updates.
* Notification: Handles operations related to user notifications, including sending out notifications for order updates, promotions, and other relevant information.
* Product: Manages all aspects related to products, including product creation, editing, categorization, and attributes.
* Catalog: Handles the listing and presentation of products, providing features such as search, filtering, and sorting for users to browse and explore.
* Cart: Deals with operations related to the shopping cart, allowing users to add, remove, and modify items before proceeding to checkout.
* Inventory: Manages the control and tracking of product inventory, including stock levels, replenishment, and availability.
* Reviews: Handles customer reviews, comments, and ratings for products, allowing users to share their experiences and opinions.
* Coupons: Manages promotional campaigns, discounts, and coupon codes to attract and incentivize customers.
* Reports: Provides reporting and analytics capabilities, allowing stakeholders to gain insights into sales, customer behavior, and other relevant metrics.
* Sales: Handles integrations with sales tools and platforms, facilitating processes such as order synchronization, inventory management, and sales data analysis.
* Campaign: Manages integrations with marketing tools and platforms, enabling targeted marketing campaigns, customer segmentation, and automation.

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
{
  "name": "Test",
  "uri": "/test",
  "price": 10000,
  "direct_sales": 0,
  "description": {"content": "Teste", "composition": "test composition", "how_to_use": "test how to use"},
  "image_path": "https://i.pinimg.com/originals/e4/34/2a/e4342a4e0e968344b75cf50cf1936c09.jpg",
  "installments_config": 1,
  "category_id": 1,
  "discount": 100,
  "sku": "sku0"
}
```

## Integrations
* Sendgrid
* Pagarme
* Mercado Pago
* Stripe
* Correios
* Tallos

## API Structure
- app
  -- infra
     -- db
     -- enpoints
        -- schemas
     -- redis
     -- gateways
        -- payment
        -- mail
        -- whatsapp
     -- workers
 -- entities -> Business rules
  -- user
     -- service -> application orchestration
     -- repository -> queries
  -- direct_sales
  -- payment
  -- order
  -- freight
  -- infra
  -- infra
  -- notification
  -- product
  -- catalog
  -- cart
  -- inventory
  -- coupons
  -- reports
  -- sales
  -- campaign
- tests

## Technologies
+ [PostgreSql](https://www.postgresql.org/)
+ [FastApi](https://fastapi.tiangolo.com/)
+ [DynaConf](https://www.dynaconf.com/)
+ [FastStrean](https://faststream.airt.ai/latest/)
