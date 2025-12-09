#!/bin/bash


BASE_URL="${BASE_URL:-http://localhost:8001}"
USER=""
PASS=""

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
            echo "Usage: $0 --user ADMIN_USERNAME --pass ADMIN_PASSWORD"
            exit 1
            ;;
    esac
done

if [ -z "$USER" ] || [ -z "$PASS" ]; then
    echo "Error: --user and --pass are required"
    echo "Usage: $0 --user ADMIN_USERNAME --pass ADMIN_PASSWORD"
    exit 1
fi

echo "🚀 Criando projeto de crowdfunding..."
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
    "end_date": "$(date -u -d "+30 days" +"%Y-%m-%dT%H:%M:%S")",
    "goal_amount": 10000.00,
    "active": true,
    "published": true
}
EOF
)

PROJECT_RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" -X POST "$BASE_URL/crowdfunding/projects" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "$PROJECT_JSON")

HTTP_CODE=$(echo "$PROJECT_RESPONSE" | grep "HTTP_CODE:" | cut -d: -f2)
PROJECT_BODY=$(echo "$PROJECT_RESPONSE" | sed '/HTTP_CODE:/d')

if [ "$HTTP_CODE" != "201" ]; then
    echo "❌ Erro ao criar projeto (HTTP $HTTP_CODE): $PROJECT_BODY"
    exit 1
fi

PROJECT_ID=$(echo "$PROJECT_BODY" | jq -r '.project_id // .id // empty' 2>/dev/null)

if [ -z "$PROJECT_ID" ] || [ "$PROJECT_ID" = "null" ]; then
    echo "❌ Erro ao extrair project_id da resposta: $PROJECT_BODY"
    exit 1
fi

echo "✅ Projeto criado com sucesso!"
echo "📋 Detalhes do projeto:"
echo "$PROJECT_RESPONSE" | jq '.'
echo ""
echo "Project ID: $PROJECT_ID"
echo "Project Slug: $PROJECT_SLUG"
echo ""

echo "4️⃣ Criando tier..."
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

TIER_RESPONSE=$(curl -s -X POST "$BASE_URL/crowdfunding/tiers" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "$TIER_JSON")

TIER_ID=$(echo $TIER_RESPONSE | jq -r '.tier_id // empty')

if [ -z "$TIER_ID" ] || [ "$TIER_ID" = "null" ]; then
    echo "⚠️ Erro ao criar tier: $TIER_RESPONSE"
else
    echo "✅ Tier criado com sucesso!"
    echo "Tier ID: $TIER_ID"
fi

echo ""
echo "🎉 Projeto criado com sucesso!"
echo ""
echo "📝 Resumo:"
echo "  - Project ID: $PROJECT_ID"
echo "  - Project Slug: $PROJECT_SLUG"
echo "  - Tier ID: ${TIER_ID:-N/A}"
echo ""
echo "🌐 Acesse o projeto em: $BASE_URL/crowdfunding/projects/slug/$PROJECT_SLUG"
