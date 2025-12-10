#!/bin/bash

BASE_URL="${BASE_URL:-http://localhost:8001}"
USER=""
PASS=""
PROJECT_ID=""
TIER_ID=""

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
        --project-id)
            PROJECT_ID="$2"
            shift 2
            ;;
        --tier-id)
            TIER_ID="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 --user USERNAME --pass PASSWORD --project-id PROJECT_ID --tier-id TIER_ID"
            exit 1
            ;;
    esac
done

if [ -z "$USER" ] || [ -z "$PASS" ] || [ -z "$PROJECT_ID" ] || [ -z "$TIER_ID" ]; then
    echo "Error: --user, --pass, --project-id and --tier-id are required"
    echo "Usage: $0 --user USERNAME --pass PASSWORD --project-id PROJECT_ID --tier-id TIER_ID"
    exit 1
fi

echo "🚀 Fazendo contribuição via PIX em projeto de crowdfunding..."
echo "User: $USER"
echo "Project ID: $PROJECT_ID"
echo "Tier ID: $TIER_ID"
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

echo "2️⃣ Obtendo informações do tier..."
TIER_INFO=$(curl -s -X GET "$BASE_URL/crowdfunding/tiers/$TIER_ID" \
    -H "Authorization: Bearer $TOKEN")

TIER_AMOUNT=$(echo "$TIER_INFO" | jq -r '.amount // empty' 2>/dev/null)

if [ -z "$TIER_AMOUNT" ] || [ "$TIER_AMOUNT" = "null" ]; then
    echo "❌ Erro ao obter tier: $TIER_INFO"
    exit 1
fi

echo "✅ Tier encontrado - Valor: R$ $TIER_AMOUNT"
echo ""

echo "3️⃣ Realizando contribuição via PIX..."
CONTRIBUTION_JSON=$(cat <<EOF
{
    "project_id": $PROJECT_ID,
    "tier_id": $TIER_ID,
    "amount": $TIER_AMOUNT,
    "is_recurring": false,
    "payment_method_id": "pix",
    "payment_gateway": "MERCADOPAGO",
    "installments": 1,
    "anonymous": false
}
EOF
)

CONTRIBUTION_RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" -X POST "$BASE_URL/crowdfunding/contributions" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "$CONTRIBUTION_JSON")

HTTP_CODE=$(echo "$CONTRIBUTION_RESPONSE" | grep "HTTP_CODE:" | cut -d: -f2)
CONTRIBUTION_BODY=$(echo "$CONTRIBUTION_RESPONSE" | sed '/HTTP_CODE:/d')

if [ "$HTTP_CODE" != "201" ]; then
    echo "❌ Erro ao fazer contribuição (HTTP $HTTP_CODE): $CONTRIBUTION_BODY"
    exit 1
fi

CONTRIBUTION_ID=$(echo "$CONTRIBUTION_BODY" | jq -r '.contribution_id // empty' 2>/dev/null)

if [ -z "$CONTRIBUTION_ID" ] || [ "$CONTRIBUTION_ID" = "null" ]; then
    echo "❌ Erro ao extrair contribution_id da resposta: $CONTRIBUTION_BODY"
    exit 1
fi

echo "✅ Contribuição via PIX realizada com sucesso!"
echo ""
echo "📋 Detalhes da contribuição:"
echo "$CONTRIBUTION_BODY" | jq '.'
echo ""
echo "🎉 Contribuição concluída com sucesso!"
echo ""
echo "📝 Resumo:"
echo "  - Contribution ID: $CONTRIBUTION_ID"
echo "  - Amount: R$ $TIER_AMOUNT"
echo "  - Payment Gateway: MERCADOPAGO (PIX)"
echo "  - Status: $(echo "$CONTRIBUTION_BODY" | jq -r '.status // "N/A"')"
echo ""
echo "💡 Verifique o status do pagamento PIX no backend ou no painel do Mercado Pago"
