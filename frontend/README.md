# Crowdfunding Frontend

Frontend para o sistema de crowdfunding, construído com SvelteKit.

## Desenvolvimento

```bash
npm install
npm run dev
```

## Testes

```bash
# Rodar testes
npm test

# Rodar testes em modo watch
npm run test:watch

# Rodar testes com cobertura (80% mínimo)
npm run test:coverage

# Interface visual dos testes
npm run test:ui
```

## Linting e Formatação

```bash
# Verificar lint
npm run lint

# Corrigir lint automaticamente
npm run lint:fix

# Verificar formatação
npm run format:check

# Formatar código
npm run format
```

## Husky Pre-commit

O Husky está configurado para rodar automaticamente antes de cada commit:
- Linter (ESLint)
- Testes com cobertura mínima de 80%

## Estrutura

- `src/lib/api.js` - Cliente API para comunicação com backend
- `src/lib/components/` - Componentes reutilizáveis
- `src/routes/` - Páginas e rotas
- `src/tests/` - Testes unitários

## Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto:

```
VITE_API_BASE_URL=http://localhost:8001
VITE_STRIPE_PUBLIC_KEY=pk_test_...
```
