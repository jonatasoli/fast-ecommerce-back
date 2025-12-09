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
ADMIN_USER=""
ADMIN_PASS=""
USER=""
PASS=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --admin-user)
            ADMIN_USER="$2"
            shift 2
            ;;
        --admin-pass)
            ADMIN_PASS="$2"
            shift 2
            ;;
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
            echo "Usage: $0 --admin-user ADMIN_USERNAME --admin-pass ADMIN_PASSWORD --user USERNAME --pass PASSWORD"
            exit 1
            ;;
    esac
done

if [ -z "$ADMIN_USER" ] || [ -z "$ADMIN_PASS" ] || [ -z "$USER" ] || [ -z "$PASS" ]; then
    echo "Error: --admin-user, --admin-pass, --user and --pass are required"
    echo "Usage: $0 --admin-user ADMIN_USERNAME --admin-pass ADMIN_PASSWORD --user USERNAME --pass PASSWORD"
    exit 1
fi

echo "🚀 Teste completo de crowdfunding"
echo "Admin: $ADMIN_USER"
echo "User: $USER"
echo ""


echo "════════════════════════════════════════"
echo "PARTE 1: Criando projeto (Admin)"
echo "════════════════════════════════════════"
echo ""

echo "1️⃣ Fazendo login como admin..."
ADMIN_TOKEN_RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" -X POST "$BASE_URL/user/token" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "grant_type=password&username=$ADMIN_USER&password=$ADMIN_PASS&scope=&client_id=string&client_secret=")

ADMIN_HTTP_CODE=$(echo "$ADMIN_TOKEN_RESPONSE" | grep "HTTP_CODE:" | cut -d: -f2)
ADMIN_TOKEN_BODY=$(echo "$ADMIN_TOKEN_RESPONSE" | sed '/HTTP_CODE:/d')

if [ "$ADMIN_HTTP_CODE" != "200" ]; then
    echo "❌ Erro no login do admin (HTTP $ADMIN_HTTP_CODE): $ADMIN_TOKEN_BODY"
    exit 1
fi

ADMIN_TOKEN=$(echo "$ADMIN_TOKEN_BODY" | jq -r '.access_token // empty' 2>/dev/null)

if [ -z "$ADMIN_TOKEN" ] || [ "$ADMIN_TOKEN" = "null" ]; then
    echo "❌ Erro no login do admin: $ADMIN_TOKEN_BODY"
    exit 1
fi

echo "✅ Login do admin realizado com sucesso"
echo ""

echo "2️⃣ Criando projeto..."
PROJECT_SLUG="projeto-teste-$(date +%s)"

PROJECT_JSON=$(cat <<EOF
{
    "title": "Projeto de Teste",
    "slug": "$PROJECT_SLUG",
    "short_description": "Descrição curta do projeto de teste",
    "description": {
        "text": "Descrição completa do projeto"
    },
    "story": {
        "text": "História do projeto"
    },
    "risks_and_challenges": {
        "text": "Riscos e desafios do projeto"
    },
    "main_image": "https://via.placeholder.com/800x400",
    "video_url": "",
    "category": "Tecnologia",
    "location": "São Paulo, Brasil",
    "start_date": "$(date -u +"%Y-%m-%dT%H:%M:%S")",
    "end_date": "$(date -u -d "+30 days" +"%Y-%m-%dT%H:%M:%S" 2>/dev/null || date -u -v+30d +"%Y-%m-%dT%H:%M:%S" 2>/dev/null || date -u +"%Y-%m-%dT%H:%M:%S")",
    "goal_amount": 10000.00,
    "active": true,
    "published": true
}
EOF
)

PROJECT_RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" -X POST "$BASE_URL/crowdfunding/projects" \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    -H "Content-Type: application/json" \
    -d "$PROJECT_JSON")

PROJECT_HTTP_CODE=$(echo "$PROJECT_RESPONSE" | grep "HTTP_CODE:" | cut -d: -f2)
PROJECT_BODY=$(echo "$PROJECT_RESPONSE" | sed '/HTTP_CODE:/d')

if [ "$PROJECT_HTTP_CODE" != "201" ]; then
    echo "❌ Erro ao criar projeto (HTTP $PROJECT_HTTP_CODE): $PROJECT_BODY"
    exit 1
fi

PROJECT_ID=$(echo "$PROJECT_BODY" | jq -r '.project_id // .id // empty' 2>/dev/null)

if [ -z "$PROJECT_ID" ] || [ "$PROJECT_ID" = "null" ]; then
    echo "❌ Erro ao extrair project_id da resposta: $PROJECT_BODY"
    exit 1
fi

echo "✅ Projeto criado com sucesso!"
echo "   Project ID: $PROJECT_ID"
echo "   Project Slug: $PROJECT_SLUG"
echo ""

echo "3️⃣ Criando tier..."
TIER_JSON=$(cat <<EOF
{
    "project_id": $PROJECT_ID,
    "name": "Apoiador Básico",
    "description": "Tier básico de apoio",
    "amount": 50.00,
    "is_recurring": false,
    "max_backers": null,
    "active": true,
    "order": 1
}
EOF
)

TIER_RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" -X POST "$BASE_URL/crowdfunding/tiers" \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    -H "Content-Type: application/json" \
    -d "$TIER_JSON")

TIER_HTTP_CODE=$(echo "$TIER_RESPONSE" | grep "HTTP_CODE:" | cut -d: -f2)
TIER_BODY=$(echo "$TIER_RESPONSE" | sed '/HTTP_CODE:/d')

if [ "$TIER_HTTP_CODE" != "201" ]; then
    echo "❌ Erro ao criar tier (HTTP $TIER_HTTP_CODE): $TIER_BODY"
    exit 1
fi

TIER_ID=$(echo "$TIER_BODY" | jq -r '.tier_id // .id // empty' 2>/dev/null)

if [ -z "$TIER_ID" ] || [ "$TIER_ID" = "null" ]; then
    echo "❌ Erro ao extrair tier_id da resposta: $TIER_BODY"
    exit 1
fi

echo "✅ Tier criado com sucesso!"
echo "   Tier ID: $TIER_ID"
echo ""


echo "════════════════════════════════════════"
echo "PARTE 2: Fazendo contribuição (User)"
echo "════════════════════════════════════════"
echo ""

echo "4️⃣ Fazendo login como usuário..."
USER_TOKEN_RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" -X POST "$BASE_URL/user/token" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "grant_type=password&username=$USER&password=$PASS&scope=&client_id=string&client_secret=")

USER_HTTP_CODE=$(echo "$USER_TOKEN_RESPONSE" | grep "HTTP_CODE:" | cut -d: -f2)
USER_TOKEN_BODY=$(echo "$USER_TOKEN_RESPONSE" | sed '/HTTP_CODE:/d')

if [ "$USER_HTTP_CODE" != "200" ]; then
    echo "❌ Erro no login do usuário (HTTP $USER_HTTP_CODE): $USER_TOKEN_BODY"
    exit 1
fi

USER_TOKEN=$(echo "$USER_TOKEN_BODY" | jq -r '.access_token // empty' 2>/dev/null)

if [ -z "$USER_TOKEN" ] || [ "$USER_TOKEN" = "null" ]; then
    echo "❌ Erro no login do usuário: $USER_TOKEN_BODY"
    exit 1
fi

echo "✅ Login do usuário realizado com sucesso"
echo ""

echo "5️⃣ Obtendo informações do tier..."
TIER_INFO=$(curl -s -X GET "$BASE_URL/crowdfunding/tiers/$TIER_ID" \
    -H "Authorization: Bearer $USER_TOKEN")

TIER_AMOUNT=$(echo "$TIER_INFO" | jq -r '.amount // empty' 2>/dev/null)

if [ -z "$TIER_AMOUNT" ] || [ "$TIER_AMOUNT" = "null" ]; then
    echo "❌ Erro ao obter tier: $TIER_INFO"
    exit 1
fi

echo "✅ Tier encontrado - Valor: R$ $TIER_AMOUNT"
echo ""

echo "6️⃣ Realizando contribuição..."
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

CONTRIBUTION_RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" -X POST "$BASE_URL/crowdfunding/contributions" \
    -H "Authorization: Bearer $USER_TOKEN" \
    -H "Content-Type: application/json" \
    -d "$CONTRIBUTION_JSON")

CONTRIBUTION_HTTP_CODE=$(echo "$CONTRIBUTION_RESPONSE" | grep "HTTP_CODE:" | cut -d: -f2)
CONTRIBUTION_BODY=$(echo "$CONTRIBUTION_RESPONSE" | sed '/HTTP_CODE:/d')

if [ "$CONTRIBUTION_HTTP_CODE" != "201" ]; then
    echo "❌ Erro ao fazer contribuição (HTTP $CONTRIBUTION_HTTP_CODE): $CONTRIBUTION_BODY"
    exit 1
fi

CONTRIBUTION_ID=$(echo "$CONTRIBUTION_BODY" | jq -r '.contribution_id // .id // empty' 2>/dev/null)

if [ -z "$CONTRIBUTION_ID" ] || [ "$CONTRIBUTION_ID" = "null" ]; then
    echo "❌ Erro ao extrair contribution_id da resposta: $CONTRIBUTION_BODY"
    exit 1
fi

echo "✅ Contribuição realizada com sucesso!"
echo ""


echo "════════════════════════════════════════"
echo "🎉 TESTE COMPLETO FINALIZADO COM SUCESSO!"
echo "════════════════════════════════════════"
echo ""
echo "📝 Resumo:"
echo "  - Project ID: $PROJECT_ID"
echo "  - Project Slug: $PROJECT_SLUG"
echo "  - Tier ID: $TIER_ID"
echo "  - Contribution ID: $CONTRIBUTION_ID"
echo "  - Amount: R$ $TIER_AMOUNT"
echo ""
echo "🌐 Acesse o projeto em: $BASE_URL/crowdfunding/projects/slug/$PROJECT_SLUG"
echo ""
