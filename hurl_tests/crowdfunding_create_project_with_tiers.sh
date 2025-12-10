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

echo "🚀 Criando projeto de crowdfunding com 10 tiers..."
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
PROJECT_SLUG="projeto-com-tiers-$(date +%s)"

PROJECT_JSON=$(cat <<EOF
{
    "title": "Projeto com Múltiplos Tiers",
    "slug": "$PROJECT_SLUG",
    "short_description": "Projeto de teste com 10 tiers diferentes",
    "description": {
        "text": "Descrição completa do projeto de teste com múltiplos tiers"
    },
    "story": {
        "text": "História do projeto de teste"
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
    "goal_amount": 50000.00,
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
echo "📋 Project ID: $PROJECT_ID"
echo "📋 Project Slug: $PROJECT_SLUG"
echo ""

echo "3️⃣ Criando 10 tiers..."
TIER_IDS=()

# Array com os tiers
TIERS=(
    '{"name":"Apoiador Básico","description":"Apoio básico ao projeto","amount":25.00,"is_recurring":false,"max_backers":null,"active":true,"order":1}'
    '{"name":"Apoiador Bronze","description":"Apoio nível bronze","amount":50.00,"is_recurring":false,"max_backers":100,"active":true,"order":2}'
    '{"name":"Apoiador Prata","description":"Apoio nível prata","amount":100.00,"is_recurring":false,"max_backers":50,"active":true,"order":3}'
    '{"name":"Apoiador Ouro","description":"Apoio nível ouro","amount":250.00,"is_recurring":false,"max_backers":30,"active":true,"order":4}'
    '{"name":"Apoiador Platina","description":"Apoio nível platina","amount":500.00,"is_recurring":false,"max_backers":20,"active":true,"order":5}'
    '{"name":"Apoiador Diamante","description":"Apoio nível diamante","amount":1000.00,"is_recurring":false,"max_backers":10,"active":true,"order":6}'
    '{"name":"Apoiador Mensal Básico","description":"Apoio mensal básico","amount":30.00,"is_recurring":true,"max_backers":null,"active":true,"order":7}'
    '{"name":"Apoiador Mensal Premium","description":"Apoio mensal premium","amount":150.00,"is_recurring":true,"max_backers":50,"active":true,"order":8}'
    '{"name":"Apoiador Mensal VIP","description":"Apoio mensal VIP","amount":500.00,"is_recurring":true,"max_backers":20,"active":true,"order":9}'
    '{"name":"Apoiador Patrocinador","description":"Apoio de patrocinador","amount":2000.00,"is_recurring":false,"max_backers":5,"active":true,"order":10}'
)

for i in "${!TIERS[@]}"; do
    TIER_NUM=$((i + 1))
    TIER_JSON=$(echo "${TIERS[$i]}" | jq --arg project_id "$PROJECT_ID" '. + {project_id: ($project_id | tonumber)}')
    
    echo "   Criando tier $TIER_NUM/10..."
    TIER_RESPONSE=$(curl -s -X POST "$BASE_URL/crowdfunding/tiers" \
        -H "Authorization: Bearer $TOKEN" \
        -H "Content-Type: application/json" \
        -d "$TIER_JSON")
    
    TIER_ID=$(echo "$TIER_RESPONSE" | jq -r '.tier_id // empty' 2>/dev/null)
    
    if [ -z "$TIER_ID" ] || [ "$TIER_ID" = "null" ]; then
        echo "   ⚠️  Erro ao criar tier $TIER_NUM: $TIER_RESPONSE"
    else
        TIER_IDS+=("$TIER_ID")
        TIER_NAME=$(echo "$TIER_JSON" | jq -r '.name')
        TIER_AMOUNT=$(echo "$TIER_JSON" | jq -r '.amount')
        echo "   ✅ Tier $TIER_NUM criado: $TIER_NAME (R$ $TIER_AMOUNT) - ID: $TIER_ID"
    fi
done

echo ""
echo "🎉 Projeto criado com sucesso!"
echo ""
echo "📝 Resumo:"
echo "  - Project ID: $PROJECT_ID"
echo "  - Project Slug: $PROJECT_SLUG"
echo "  - Tiers criados: ${#TIER_IDS[@]}/10"
echo ""
echo "📋 IDs dos Tiers:"
for i in "${!TIER_IDS[@]}"; do
    echo "  Tier $((i + 1)): ${TIER_IDS[$i]}"
done
echo ""
echo "🌐 Acesse o projeto em: $BASE_URL/crowdfunding/projects/slug/$PROJECT_SLUG"
echo ""
echo "💡 Para fazer uma contribuição, use:"
echo "   ./hurl_tests/crowdfunding_contribute_pix.sh --user $USER --pass [PASSWORD] --project-id $PROJECT_ID --tier-id ${TIER_IDS[0]}"
echo "   ./hurl_tests/crowdfunding_contribute_stripe.sh --user $USER --pass [PASSWORD] --project-id $PROJECT_ID --tier-id ${TIER_IDS[0]}"
