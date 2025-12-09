# Scripts de Teste Hurl

Scripts para testar os fluxos completos do sistema de ecommerce e crowdfunding.

## Pré-requisitos

- `curl` instalado
- `jq` instalado (para parsing JSON)
- Servidor rodando em `http://localhost:8000` (ou configure `BASE_URL`)

## Scripts Disponíveis

### Ecommerce

#### 1. Checkout com Cartão de Crédito (Stripe)
```bash
./ecommerce_checkout_credit_card.sh --user USERNAME --pass PASSWORD
```

Testa o fluxo completo:
1. Login
2. Criar carrinho
3. Adicionar produto
4. Adicionar usuário
5. Adicionar endereço
6. Adicionar pagamento (Stripe)
7. Preview
8. Checkout

**Nota:** O script usa um token de exemplo `pm_card_visa`. Para testar com tokens reais, você precisa:
- Configurar Stripe Elements no frontend
- Obter um PaymentMethod ID válido
- Substituir no script

#### 2. Checkout com PIX
```bash
./ecommerce_checkout_pix.sh --user USERNAME --pass PASSWORD
```

Testa o fluxo completo com pagamento PIX via Mercado Pago.

### Crowdfunding

#### 3. Criar Projeto (Admin)
```bash
./crowdfunding_create_project.sh --user ADMIN_USERNAME --pass ADMIN_PASSWORD
```

Cria um projeto de crowdfunding completo:
1. Login como admin
2. Criar projeto
3. Criar tier básico

**Retorna:**
- Project ID
- Project Slug
- Tier ID

#### 4. Fazer Contribuição
```bash
./crowdfunding_contribute.sh --user USERNAME --pass PASSWORD --project-id PROJECT_ID --tier-id TIER_ID
```

Faz uma contribuição em um projeto:
1. Login
2. Obter informações do tier
3. Fazer contribuição via Stripe

**Nota:** O script usa um token de exemplo. Para testar com tokens reais, você precisa de um PaymentMethod ID válido do Stripe.

## Variáveis de Ambiente

Você pode configurar a URL base do servidor:

```bash
export BASE_URL=http://localhost:8000
./ecommerce_checkout_credit_card.sh --user user --pass pass
```

## Exemplos de Uso

### Teste completo de ecommerce com cartão
```bash
./ecommerce_checkout_credit_card.sh --user 12345678901 --pass senha123
```

### Teste completo de ecommerce com PIX
```bash
./ecommerce_checkout_pix.sh --user 12345678901 --pass senha123
```

### Criar projeto de crowdfunding
```bash
./crowdfunding_create_project.sh --user admin --pass admin123
```

### Fazer contribuição (após criar projeto)
```bash
# Primeiro, crie o projeto e anote o PROJECT_ID e TIER_ID
./crowdfunding_contribute.sh --user user123 --pass senha123 --project-id 1 --tier-id 1
```

## Troubleshooting

### Erro: "jq: command not found"
Instale o jq:
```bash
# Ubuntu/Debian
sudo apt-get install jq

# macOS
brew install jq
```

### Erro: "Token inválido"
- Verifique se o usuário e senha estão corretos
- Verifique se o servidor está rodando
- Verifique se a URL base está correta

### Erro: "Product not found"
- Certifique-se de que existe um produto com ID 1 no banco
- Ou ajuste a variável `PRODUCT_ID` no script

### Erro: "PaymentMethod inválido"
- Os scripts usam tokens de exemplo
- Para testar com tokens reais, você precisa:
  1. Configurar Stripe Elements no frontend
  2. Obter um PaymentMethod ID válido
  3. Substituir no script

## Notas Importantes

1. **Tokens de Pagamento**: Os scripts usam tokens de exemplo. Em produção, você precisa de tokens reais do Stripe Elements.

2. **Product ID**: O script assume que existe um produto com ID 1. Ajuste conforme necessário.

3. **User ID**: Alguns scripts tentam obter o user_id automaticamente. Se falhar, usa 1 como padrão.

4. **Stripe**: Para testar pagamentos reais, você precisa:
   - Configurar as chaves do Stripe
   - Usar tokens de teste do Stripe
   - Ou usar o Stripe Elements no frontend para gerar tokens válidos
