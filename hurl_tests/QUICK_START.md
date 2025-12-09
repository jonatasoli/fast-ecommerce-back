# Guia Rápido - Scripts de Teste

## 🚀 Uso Rápido

### Ecommerce - Checkout com Cartão (Stripe)
```bash
cd hurl_tests
./ecommerce_checkout_credit_card.sh --user SEU_CPF --pass SUA_SENHA
```

### Ecommerce - Checkout com PIX
```bash
./ecommerce_checkout_pix.sh --user SEU_CPF --pass SUA_SENHA
```

### Crowdfunding - Criar Projeto (Admin)
```bash
./crowdfunding_create_project.sh --user ADMIN_CPF --pass ADMIN_SENHA
```

### Crowdfunding - Fazer Contribuição
```bash
./crowdfunding_contribute.sh --user USER_CPF --pass USER_SENHA --project-id 1 --tier-id 1
```

## 📋 Fluxo Completo de Teste

### 1. Teste Ecommerce Completo

```bash
# Teste com cartão de crédito
./ecommerce_checkout_credit_card.sh --user 12345678901 --pass senha123

# Teste com PIX
./ecommerce_checkout_pix.sh --user 12345678901 --pass senha123
```

### 2. Teste Crowdfunding Completo

```bash
# 1. Criar projeto (como admin)
./crowdfunding_create_project.sh --user 12345678901 --pass admin123

# Anote o PROJECT_ID e TIER_ID retornados

# 2. Fazer contribuição (como usuário)
./crowdfunding_contribute.sh --user 98765432100 --pass senha123 --project-id 1 --tier-id 1
```

## ⚙️ Configuração

### Variáveis de Ambiente

```bash
# Configurar URL do servidor (opcional)
export BASE_URL=http://localhost:8000

# Configurar ID do produto (opcional, padrão: 1)
export PRODUCT_ID=1
```

## 🔧 Requisitos

- `curl` - Para fazer requisições HTTP
- `jq` - Para parsing JSON (instalar: `sudo apt-get install jq` ou `brew install jq`)

## 📝 Notas Importantes

1. **Tokens de Pagamento**: Os scripts usam tokens de exemplo (`pm_card_visa`). Para testar com tokens reais:
   - Configure Stripe Elements no frontend
   - Obtenha um PaymentMethod ID válido
   - Substitua no script

2. **User ID**: O backend obtém automaticamente do token, não é necessário enviar.

3. **Product ID**: O script assume produto ID 1. Ajuste a variável `PRODUCT_ID` se necessário.

## 🐛 Troubleshooting

### Erro: "jq: command not found"
```bash
# Ubuntu/Debian
sudo apt-get install jq

# macOS
brew install jq
```

### Erro: "Token inválido"
- Verifique usuário e senha
- Verifique se o servidor está rodando
- Verifique a URL base

### Erro: "Product not found"
- Certifique-se de que existe produto com ID 1
- Ou ajuste `PRODUCT_ID` no script
