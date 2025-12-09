#!/bin/bash


if [ -f "$(dirname "$0")/../.env.test" ]; then
    set -a
    source "$(dirname "$0")/../.env.test"
    set +a
fi

if [ -z "$STRIPE_SECRET_KEY" ] && [ -f "$(dirname "$0")/../.secrets.toml" ]; then
    STRIPE_SECRET_KEY=$(grep -E '^STRIPE_SECRET_KEY\s*=' "$(dirname "$0")/../.secrets.toml" | sed -E 's/^STRIPE_SECRET_KEY\s*=\s*"([^"]+)".*/\1/' | head -1)
fi

create_stripe_payment_method() {
    if [ -z "$STRIPE_SECRET_KEY" ]; then
        echo "pm_card_visa"
        return 0
    fi
    
    local card_number="${1:-4242424242424242}"
    local exp_month="${2:-12}"
    local exp_year="${3:-2025}"
    local cvc="${4:-123}"
    
    local response=$(curl -s -X POST "https://api.stripe.com/v1/payment_methods" \
        -u "$STRIPE_SECRET_KEY:" \
        -d "type=card" \
        -d "card[number]=$card_number" \
        -d "card[exp_month]=$exp_month" \
        -d "card[exp_year]=$exp_year" \
        -d "card[cvc]=$cvc")
    
    local payment_method_id=$(echo "$response" | jq -r '.id // empty' 2>/dev/null)
    local error=$(echo "$response" | jq -r '.error.message // empty' 2>/dev/null)
    
    if [ -z "$payment_method_id" ] || [ "$payment_method_id" = "null" ]; then
        if [ -n "$error" ]; then
            echo "⚠️  Erro ao criar PaymentMethod do Stripe: $error" >&2
        fi
        echo "pm_card_visa"
        return 1
    fi
    
    echo "$payment_method_id"
}

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

echo "🚀 Fazendo contribuição em projeto de crowdfunding..."
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

TIER_AMOUNT=$(echo $TIER_INFO | jq -r '.amount // empty')

if [ -z "$TIER_AMOUNT" ] || [ "$TIER_AMOUNT" = "null" ]; then
    echo "❌ Erro ao obter tier: $TIER_INFO"
    exit 1
fi

echo "✅ Tier encontrado - Valor: R$ $TIER_AMOUNT"
echo ""

echo "3️⃣ Preparando contribuição..."
echo "✅ O backend obterá o user_id do token automaticamente"
echo ""

echo "4️⃣ Realizando contribuição..."
echo "   Criando PaymentMethod de cartão no Stripe..."
STRIPE_TOKEN=$(create_stripe_payment_method "4242424242424242" "12" "2025" "123")

if [ "$STRIPE_TOKEN" = "pm_card_visa" ]; then
    echo "   ℹ️  Usando PaymentMethod ID de teste padrão (pm_card_visa)"
    echo "   💡 Para criar um token real, defina STRIPE_SECRET_KEY como variável de ambiente"
else
    echo "   ✅ Token criado: $STRIPE_TOKEN"
fi

CONTRIBUTION_JSON=$(cat <<EOF
{
    "project_id": $PROJECT_ID,
    "tier_id": $TIER_ID,
    "amount": $TIER_AMOUNT,
    "is_recurring": false,
    "payment_method_id": "$STRIPE_TOKEN",
    "payment_gateway": "STRIPE",
    "installments": 1,
    "anonymous": false
}
EOF
)

CONTRIBUTION_RESPONSE=$(curl -s -X POST "$BASE_URL/crowdfunding/contributions" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "$CONTRIBUTION_JSON")

CONTRIBUTION_ID=$(echo $CONTRIBUTION_RESPONSE | jq -r '.contribution_id // empty')

if [ -z "$CONTRIBUTION_ID" ] || [ "$CONTRIBUTION_ID" = "null" ]; then
    echo "❌ Erro ao fazer contribuição: $CONTRIBUTION_RESPONSE"
    exit 1
fi

echo "✅ Contribuição realizada com sucesso!"
echo ""
echo "📋 Detalhes da contribuição:"
echo "$CONTRIBUTION_RESPONSE" | jq '.'
echo ""
echo "🎉 Contribuição concluída com sucesso!"
echo ""
echo "📝 Resumo:"
echo "  - Contribution ID: $CONTRIBUTION_ID"
echo "  - Amount: R$ $TIER_AMOUNT"
echo "  - Status: $(echo $CONTRIBUTION_RESPONSE | jq -r '.status')"
