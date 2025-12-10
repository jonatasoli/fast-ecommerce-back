[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=jonatasoli_fast-ecommerce-back&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=jonatasoli_fast-ecommerce-back)
[![Coverage](https://sonarcloud.io/api/project_badges/measure?project=jonatasoli_fast-ecommerce-back&metric=coverage)](https://sonarcloud.io/summary/new_code?id=jonatasoli_fast-ecommerce-back)
# Capicart Backend

 [Pre-requirements](#pre-requirements)
 [Install](#install)
 [Technologies](#technologies)

## Pre-requirements
+ Docker and docker-compose
+ Install [uv](https://docs.astral.sh/uv/getting-started/installation/)
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```
+ Repository clone
```bash
git clone https://github.com/jonatasoli/fast-ecommerce-back.git
```
```bash
cd fast-ecommerce-back
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
```bash
uv sync
```

## Required Environment Variables

Before starting the project, configure the following environment variables in the `.secrets.toml` file:

### Minimum Required Configuration

```toml
[default]
# Database (required)
DATABASE_URL="postgresql+psycopg://user:password@localhost/database_name"
DATABASE_URI="postgresql+asyncpg://user:password@localhost/database_name"

# Security (required)
SECRET_KEY="your_random_secret_key_here"  # Use a strong random key
CONFIRMATION_KEY="your_random_confirmation_key_here"  # Use a strong random key
CAPI_SECRET="your_base64_encryption_key_here"  # Generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Redis (required if using cache/sessions)
REDIS_URL="redis://:@localhost:6379"
REDIS_DB=0

# Message Broker (required if using queues)
BROKER_URL="amqp://guest:guest@localhost:5672//"

# Environment
ENVIRONMENT="development"  # or "production", "testing"
```

### Additional Configuration (Optional)

The following variables can be configured later or left with default values:

- **Upload/Storage**: `ENDPOINT_UPLOAD_CLIENT`, `BUCKET_NAME`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`
- **Payments**: `STRIPE_SECRET_KEY`, `MERCADO_PAGO_ACCESS_TOKEN`, `PAYMENT_GATEWAY`
- **Logistics**: `CORREIOSBR_USER`, `CORREIOSBR_PASS`, `CORREIOSBR_API_SECRET`
- **Notifications**: `SENDGRID_API_KEY`, `EMAIL_FROM`
- **reCAPTCHA**: `RECAPTCHA_PROJECT_ID`, `RECAPTCHA_SITE_KEY`, `RECAPTCHA_SCORE_THRESHOLD`
- **Frontend/CORS**: `FRONTEND_URL`, `CORS_ORIGINS`

> **Note**: The system has fallback to environment variables when it doesn't find configurations in the database. Configurations can be managed via the admin panel after the first initialization.

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
* Crowdfunding: Manages crowdfunding projects, tiers, contributions, goals, and leaderboards. Handles project creation, backer contributions, payment processing, and project statistics tracking.
* Settings: Manages system-wide configuration settings stored in the database, including payment gateways, CDN, logistics, notifications, mail, and bucket configurations. Provides admin interface for dynamic settings management with encryption for sensitive data.

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
