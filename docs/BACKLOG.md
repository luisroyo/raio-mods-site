# 📋 Backlog de Funcionalidades — Raio Mods Site

> Arquivo de registro de ideias e funcionalidades pendentes de análise e implementação.
> Criado em: 2026-07-27

---

## 1. Analytics de Visitantes

Saber quantos usuários acessam o site por dia.

### Opção A — Google Analytics 4 (GA4) — Mais rápido
- Gratuito, sem limite de tráfego
- Adicionar 1 script no `templates/base.html`
- Mostra: visitantes por dia, país, dispositivo, páginas mais acessadas
- Sem nenhum código no backend

### Opção B — Rastreamento próprio no banco
- Criar tabela `page_visits` com IP anonimizado, página, data, país, device
- Middleware Flask registra cada visita
- Exibir no painel admin como "Visitas de Hoje / Este Mês"

**Status:** Pendente | **Prioridade:** Alta

---

## 2. Rastreamento de Cupons em Compras

Saber qual cupom o cliente usou em cada pedido aprovado.

### O que precisa:
1. Tabela `coupons` com código, desconto, limite de usos, validade
2. Campo `coupon_code` e `discount_applied` na tabela `orders`
3. Checkout captura o cupom, valida e salva junto ao pedido
4. Painel admin: filtro de vendas por cupom + relatório de uso

**Status:** Pendente | **Prioridade:** Alta

---

## 3. Cartão Internacional sem CNPJ

Aceitar cartões de crédito de qualquer país sem precisar de CNPJ.

### Opções pesquisadas:

| Gateway | Aceita PF/CPF? | Taxa | Ponto forte |
|---|---|---|---|
| **Stripe** | Sim | ~2,9% + $0,30 | Mais completo, SDK Python, cartão mundial |
| **Paddle** | Sim | ~5% + $0,50 | Merchant of Record — nota fiscal no nome deles |
| **Hotmart/Kiwify** | Sim | Variável | Mais simples, voltado para infoprodutos |
| **PayPal** | Sim | ~4,4% | Taxa alta, alguns países bloqueiam |

### Recomendação de caminho:
- **Clientes BR (BRL):** Mercado Pago — já integrado
- **Clientes internacionais (cartão):** Stripe — integrar após Binance Pay
- **Sem querer tratar nota fiscal:** Paddle
- **Clientes crypto:** Binance Pay — já planejado

**Próximo passo:** Criar conta no Stripe, testar sandbox, integrar como 3o gateway

**Status:** Pendente análise | **Prioridade:** Alta

---

## Resumo

| # | Funcionalidade | Esforço | Status |
|---|---|---|---|
| 1 | Google Analytics 4 no site | Baixo (1h) | Pendente |
| 2 | Cupons em pedidos | Médio (1 dia) | Pendente |
| 3 | Stripe (cartão internacional) | Médio (1-2 dias) | Em análise |
