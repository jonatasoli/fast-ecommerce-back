#!/bin/bash

if [ -f "$(dirname "$0")/../.env.test" ]; then
    set -a
    source "$(dirname "$0")/../.env.test"
    set +a
fi

if [ -z "$MERCADO_PAGO_ACCESS_TOKEN" ] && [ -f "$(dirname "$0")/../.secrets.toml" ]; then
    MERCADO_PAGO_ACCESS_TOKEN=$(grep -E '^MERCADO_PAGO_ACCESS_TOKEN\s*=' "$(dirname "$0")/../.secrets.toml" | sed -E 's/^MERCADO_PAGO_ACCESS_TOKEN\s*=\s*"([^"]+)".*/\1/' | head -1)
fi

BASE_URL="${BASE_URL:-http://localhost:8001}"
USER=""
PASS=""
PRODUCT_ID="${PRODUCT_ID:-1}"

create_mercadopago_card_token() {
    if [ -z "$MERCADO_PAGO_ACCESS_TOKEN" ]; then
        echo "4509 9535 6623 3704"
        return 0
    fi
    
    local card_number="${1:-4509953566233704}"
    local exp_month="${2:-11}"
    local exp_year="${3:-2025}"
    local cvc="${4:-123}"
    local cardholder_name="${5:-APRO}"
    
    local response=$(curl -s -X POST "https://api.mercadopago.com/v1/card_tokens" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $MERCADO_PAGO_ACCESS_TOKEN" \
        -d "{
            \"card_number\": \"$card_number\",
            \"expiration_month\": $exp_month,
            \"expiration_year\": $exp_year,
            \"security_code\": \"$cvc\",
            \"cardholder\": {
                \"name\": \"$cardholder_name\"
            }
        }")
    
    local token=$(echo "$response" | jq -r '.id // empty' 2>/dev/null)
    local error=$(echo "$response" | jq -r '.message // .error // empty' 2>/dev/null)
    
    if [ -z "$token" ] || [ "$token" = "null" ]; then
        if [ -n "$error" ]; then
            echo "⚠️  Erro ao criar card token do Mercado Pago: $error" >&2
        fi
        echo "$card_number"
        return 1
    fi
    
    echo "$token"
}

while [[ $# -gt 0 ]]; do
    case $1 in
        --user)
            USER="$2"
            shift 2
            ;;
        --pass)
            PASS="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 --user USERNAME --pass PASSWORD"
            exit 1
            ;;
    esac
done

if [ -z "$USER" ] || [ -z "$PASS" ]; then
    echo "Error: --user and --pass are required"
    echo "Usage: $0 --user USERNAME --pass PASSWORD"
    exit 1
fi

echo "🚀 Iniciando teste de checkout ecommerce com PIX..."
echo "User: $USER"
echo ""

echo "1️⃣ Fazendo login..."
TOKEN_RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" -X POST "$BASE_URL/user/token" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "grant_type=password&username=$USER&password=$PASS&scope=&client_id=string&client_secret=")

HTTP_CODE=$(echo "$TOKEN_RESPONSE" | grep "HTTP_CODE:" | cut -d: -f2)
TOKEN_BODY=$(echo "$TOKEN_RESPONSE" | sed '/HTTP_CODE:/d')

if [ "$HTTP_CODE" != "200" ]; then
    echo "❌ Erro no login (HTTP $HTTP_CODE): $TOKEN_BODY"
    exit 1
fi

TOKEN=$(echo "$TOKEN_BODY" | jq -r '.access_token // empty' 2>/dev/null)

if [ -z "$TOKEN" ] || [ "$TOKEN" = "null" ]; then
    echo "❌ Erro no login: $TOKEN_BODY"
    exit 1
fi

echo "✅ Login realizado com sucesso"
echo ""

echo "2️⃣ Criando carrinho..."
CART_RESPONSE=$(curl -s -X POST "$BASE_URL/cart/" \
    -H "Authorization: Bearer $TOKEN")

CART_UUID=$(echo $CART_RESPONSE | jq -r '.uuid // empty')

if [ -z "$CART_UUID" ] || [ "$CART_UUID" = "null" ]; then
    echo "❌ Erro ao criar carrinho: $CART_RESPONSE"
    exit 1
fi

echo "✅ Carrinho criado: $CART_UUID"
echo ""

echo "3️⃣ Adicionando produto ao carrinho..."
PRODUCT_JSON=$(cat <<EOF
{
    "product_id": $PRODUCT_ID,
    "quantity": 1,
    "name": "BLOND CELEBRITY - PÓ DESCOLORANTE",
    "image_path": "http://localhost:8001/static/images/9c327cb02d5f7363.png",
    "available_quantity": 1000,
    "price": 379,
    "description": "Produto de teste",
    "discount_price": 0
}
EOF
)

ADD_PRODUCT_RESPONSE=$(curl -s -X POST "$BASE_URL/cart/$CART_UUID/product" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "$PRODUCT_JSON")

if [ -z "$ADD_PRODUCT_RESPONSE" ] || echo "$ADD_PRODUCT_RESPONSE" | jq -e '.error' > /dev/null 2>&1; then
    echo "❌ Erro ao adicionar produto: $ADD_PRODUCT_RESPONSE"
    exit 1
fi

echo "✅ Produto adicionado"
CART_BASE=$(echo "$ADD_PRODUCT_RESPONSE" | jq -c '.')
echo ""

echo "4️⃣ Adicionando usuário ao carrinho..."
CART_USER_JSON=$(echo "$CART_BASE" | jq -c '{uuid, cart_items, subtotal, total, affiliate, coupon, discount, zipcode, freight_product_code, freight}')

ADD_USER_RESPONSE=$(curl -s -X POST "$BASE_URL/cart/$CART_UUID/user" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "$CART_USER_JSON")

if [ -z "$ADD_USER_RESPONSE" ] || echo "$ADD_USER_RESPONSE" | jq -e '.error' > /dev/null 2>&1; then
    echo "❌ Erro ao adicionar usuário: $ADD_USER_RESPONSE"
    exit 1
fi

echo "✅ Usuário adicionado ao carrinho"
CART_USER=$(echo "$ADD_USER_RESPONSE" | jq -c '.')
echo ""

echo "5️⃣ Adicionando endereço..."
ADDRESS_FULL_JSON=$(cat <<EOF
{
  "cart": $(echo "$CART_USER" | jq -c '.'),
  "address": {
    "shipping_is_payment": true,
    "user_address": {
      "address_id": null,
      "user_id": null,
      "country": "Brasil",
      "city": "São Paulo",
      "state": "SP",
      "neighborhood": "Centro",
      "street": "Rua Teste",
      "street_number": "123",
      "address_complement": "Apto 45",
      "zipcode": "01310100",
      "active": true
    }
  }
}
EOF
)

ADD_ADDRESS_RESPONSE=$(curl -s -X POST "$BASE_URL/cart/$CART_UUID/address" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "$ADDRESS_FULL_JSON")

if [ -z "$ADD_ADDRESS_RESPONSE" ] || echo "$ADD_ADDRESS_RESPONSE" | jq -e '.error' > /dev/null 2>&1; then
    echo "❌ Erro ao adicionar endereço: $ADD_ADDRESS_RESPONSE"
    exit 1
fi

echo "✅ Endereço adicionado"
CART_SHIPPING=$(echo "$ADD_ADDRESS_RESPONSE" | jq -c '.')
echo ""

echo "6️⃣ Adicionando pagamento PIX..."
PAYMENT_FULL_JSON=$(cat <<EOF
{
  "cart": $(echo "$CART_SHIPPING" | jq -c '.'),
  "payment": {
    "payment_gateway": "MERCADOPAGO"
  }
}
EOF
)

ADD_PAYMENT_RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" -X POST "$BASE_URL/cart/$CART_UUID/payment/pix" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "$PAYMENT_FULL_JSON")

HTTP_CODE=$(echo "$ADD_PAYMENT_RESPONSE" | grep -o "HTTP_CODE:[0-9]*" | cut -d: -f2)
ADD_PAYMENT_BODY=$(echo "$ADD_PAYMENT_RESPONSE" | sed 's/HTTP_CODE:[0-9]*$//')

if [ "$HTTP_CODE" != "201" ] && [ "$HTTP_CODE" != "200" ]; then
    echo "❌ Erro ao adicionar pagamento (HTTP $HTTP_CODE): $ADD_PAYMENT_BODY"
    exit 1
fi

if [ -z "$ADD_PAYMENT_BODY" ] || echo "$ADD_PAYMENT_BODY" | jq -e '.error' > /dev/null 2>&1; then
    echo "❌ Erro ao adicionar pagamento: $ADD_PAYMENT_BODY"
    exit 1
fi

echo "✅ Pagamento PIX adicionado"
CART_PAYMENT=$(echo "$ADD_PAYMENT_BODY" | jq -c '.')
echo ""

echo "7️⃣ Fazendo preview do carrinho..."
PREVIEW_RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" -X GET "$BASE_URL/cart/$CART_UUID/preview" \
    -H "Authorization: Bearer $TOKEN")

HTTP_CODE=$(echo "$PREVIEW_RESPONSE" | grep "HTTP_CODE:" | cut -d: -f2)
PREVIEW_BODY=$(echo "$PREVIEW_RESPONSE" | sed '/HTTP_CODE:/d')

if [ "$HTTP_CODE" != "200" ]; then
    echo "❌ Erro no preview (HTTP $HTTP_CODE): $PREVIEW_BODY"
    exit 1
fi

if [ -z "$PREVIEW_BODY" ] || echo "$PREVIEW_BODY" | jq -e '.error' > /dev/null 2>&1; then
    echo "❌ Erro no preview: $PREVIEW_BODY"
    exit 1
fi

echo "✅ Preview realizado"
CART_PREVIEW=$(echo "$PREVIEW_BODY" | jq -c '.')
echo ""

echo "8️⃣ Realizando checkout..."
CHECKOUT_JSON=$(echo "$CART_PREVIEW" | jq -c '.')

CHECKOUT_RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" -X POST "$BASE_URL/cart/$CART_UUID/checkout" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "$CHECKOUT_JSON")

HTTP_CODE=$(echo "$CHECKOUT_RESPONSE" | grep "HTTP_CODE:" | cut -d: -f2)
CHECKOUT_BODY=$(echo "$CHECKOUT_RESPONSE" | sed '/HTTP_CODE:/d')

if [ "$HTTP_CODE" != "202" ]; then
    echo "❌ Erro no checkout (HTTP $HTTP_CODE): $CHECKOUT_BODY"
    echo "Payload enviado: $CHECKOUT_JSON"
    exit 1
fi

CHECKOUT_RESPONSE=$(curl -s -X POST "$BASE_URL/cart/$CART_UUID/checkout" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "$CHECKOUT_JSON")

echo "✅ Checkout realizado!"
echo ""
echo "📋 Resposta do checkout:"
echo "$CHECKOUT_RESPONSE" | jq '.'

echo ""
echo "🎉 Teste concluído com sucesso!"
