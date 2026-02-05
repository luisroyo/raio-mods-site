# 💰 Sistema Completo de Gerenciamento de Vendas

## 📋 Visão Geral

Seu painel admin agora possui um **Sistema Completo de Vendas** que permite:

✅ **Registrar vendas manuais** (offline, fora do site)  
✅ **Registrar vendas online** (automáticas do Mercado Pago)  
✅ **Gerenciar recargas de painel** (em dólares)  
✅ **Visualizar lucro em tempo real** (com todas as deduções)  
✅ **Histórico de todas as transações**  

---

## 🎯 Como Usar

### 1. **Acessar a Seção de Vendas & Lucros**

No painel admin, clique na aba **"💰 Vendas & Lucros"** para ver:

```
[📂 Jogos] [🛍️ Produtos] [💰 Vendas & Lucros] [🔗 Links]
```

### 2. **Registrar uma Venda Manual**

**Quando**: Quando você vende algo offline (por WhatsApp, Telegram, etc.)

**Como fazer**:
1. Preencha os campos:
   - **Produto**: Selecione qual produto foi vendido
   - **Quantidade**: Quantos itens vendeu
   - **Preço de Venda (R$)**: Quanto o cliente pagou
   - **Custo Unitário (R$)**: Quanto aquilo custou pra você
   - **Notas**: Opcional (ex: "Cliente XYZ", "Cupom 20% OFF")

2. Clique em **"💾 Registrar Venda Manual"**

**Exemplo**:
```
Produto: KOS Virtual - 30 Dias
Quantidade: 2
Preço de Venda: R$ 50,00 (por unidade)
Custo Unitário: R$ 15,00 (por unidade)
Notas: Venda pelo WhatsApp

Resultado:
- Total Venda: R$ 100,00 (2 × 50)
- Total Custo: R$ 30,00 (2 × 15)
- Lucro: R$ 70,00 ✅
```

### 3. **Registrar uma Recarga de Painel**

**Quando**: Quando você compra painéis/chaves novos em dólares

**Como fazer**:
1. Preencha os campos:
   - **Quantidade de Painéis**: Quantos painéis você comprou
   - **Custo Unitário (USD)**: Preço de cada painel em dólares
   - **Cotação USD-BRL**: A cotação que você usou (auto-preenchida)
   - **Notas**: Fornecedor, data, referência

2. Clique em **"📦 Registrar Recarga"**

**Exemplo**:
```
Quantidade: 10 painéis
Custo Unitário: $50,00 USD
Cotação: R$ 5,20
Total: $500 USD = R$ 2.600,00 BRL (com IOF 6.38%)

Resultado:
- Seu custo fixo foi registrado
- Será descontado do lucro total
```

### 4. **Visualizar Resumo em Tempo Real**

Na parte superior vê 4 cards com:

| Card | O que mostra |
|------|-------------|
| 🌐 Vendas Online | Total de vendas automáticas (Mercado Pago) |
| 🛒 Vendas Manuais | Total de vendas que você registrou offline |
| 💰 Faturamento Total | Soma de tudo (online + manual) |
| 📉 Custos Totais | Produtos importados + recargas de painel |
| 🎯 Lucro Total | Faturamento - Custos (seu ganho real) |

Clique em **"🔄 Atualizar Relatório"** para recalcular tudo em tempo real.

---

## 📊 Como os Cálculos Funcionam

### Vendas Online (Mercado Pago)
```
Faturamento = SUM(todas as vendas aprovadas em BRL)
Custo = SUM(cost_usd de cada produto × cotação × IOF 6.38%)
Lucro Online = Faturamento - Custo
```

### Vendas Manuais
```
Faturamento = SUM(quantidade × preço_venda para cada venda)
Custo = SUM(quantidade × custo_unitário para cada venda)
Lucro Manual = Faturamento - Custo
```

### Recargas de Painel
```
Custo = SUM(quantidade × custo_unitário_usd × cotação × IOF)
Este valor é descontado do lucro total
```

### Lucro Final
```
LUCRO TOTAL = (Lucro Online + Lucro Manual) - Custo Recargas
MARGEM DE LUCRO = (Lucro Total / Faturamento Total) × 100%
```

---

## 📋 Histórico de Transações

### Tabela de Vendas Manuais

Mostra todas as suas vendas offline com:
- Produto vendido
- Quantidade
- Preço unitário
- Custo unitário
- **Total Venda** (verde)
- **Lucro** (amarelo)
- Data e hora
- Botão para excluir se necessário

### Tabela de Recargas

Mostra todas as compras de painéis com:
- Quantidade comprada
- Custo unitário em USD
- Total em USD
- Cotação usada
- Total convertido para BRL (com IOF)
- Notas (fornecedor, etc)
- Data e hora
- Botão para excluir se necessário

---

## 🔧 Campos de Entrada Explicados

### Registrar Venda Manual

| Campo | Tipo | Exemplo | Explicação |
|-------|------|---------|------------|
| Produto | Select | "KOS Virtual - 30 Dias" | Escolha qual produto foi vendido |
| Quantidade | Número | 2 | Quantos itens vendeu |
| Preço de Venda | Texto | R$ 50,00 | O que o cliente pagou (aceita R$ e , .) |
| Custo Unitário | Texto | R$ 15,00 | Seu custo (aceita R$ e , .) |
| Notas | Texto | Cliente João | Informação extra (opcional) |

### Registrar Recarga

| Campo | Tipo | Exemplo | Explicação |
|-------|------|---------|------------|
| Quantidade de Painéis | Número | 10 | Quantos painéis você comprou |
| Custo Unitário (USD) | Número | 50.00 | Preço de cada painel em dólares |
| Cotação USD-BRL | Número | 5.20 | Cotação que você usou (auto-preenchida) |
| Notas | Texto | Fornecedor ABC | Referência (opcional) |

---

## 📱 Exemplo Prático Completo

**Cenário**: Você vende hacks e painéis

**Segunda-feira**:
- Compra 20 painéis em USD: $500 USD
- Registra recarga: 20 × $50 = $500 USD (R$ 2.600 com IOF)

**Terça-feira**:
- Vende 5 hacks online (site): R$ 300,00
- Vende 3 hacks offline (WhatsApp): R$ 180,00

**Relatório Final** (clique em "Atualizar"):

```
VENDAS ONLINE:        R$ 300,00 (5 vendas)
VENDAS MANUAIS:       R$ 180,00 (3 vendas)
─────────────────────────────────
FATURAMENTO TOTAL:    R$ 480,00

CUSTO PRODUTOS:       R$ 200,00 (USD + IOF)
CUSTO RECARGAS:       R$ 2.600,00
─────────────────────────────────
CUSTOS TOTAIS:        R$ 2.800,00

─────────────────────────────────
LUCRO/PREJUÍZO:       -R$ 2.320,00 ❌

Obs: Neste caso com custo alto de recarga,
você está em prejuízo. Quando vender mais,
o lucro positivo aparecerá em verde.
```

---

## 🎯 Dicas Importantes

### ✅ Preenchimento Correto

1. **Sempre complete o "Custo Unitário"** nas vendas manuais
   - Sem isso, o lucro não será calculado corretamente

2. **Use a cotação correta** nas recargas
   - Se você comprou em dólares, use a cotação que você pagou
   - Não use cotação de dias anteriores

3. **Registre as recargas assim que chegar**
   - Quanto antes, mais preciso será o relatório de lucro

### ⚠️ Situações Comuns

**P: Vendi algo, mas não tenho o produto no dropdown?**  
R: Crie o produto primeiro na seção "🛍️ Produtos Soltos" ou "📂 Jogos"

**P: Preciso editar uma venda registrada?**  
R: Clique 🗑️ para deletar e registre novamente

**P: A cotação mudou, preciso atualizar?**  
R: Não precisa dos históricos. Use a cotação atual nas próximas recargas.

---

## 💡 Estratégia Recomendada

### Diariamente
- [ ] Ao vender offline, registre a venda no painel
- [ ] Clique em "🔄 Atualizar Relatório" para ver lucro atual

### Semanalmente
- [ ] Revise o "Histórico de Vendas Manuais"
- [ ] Confirme que tudo foi registrado corretamente

### Mensalmente
- [ ] Exporte ou tire print do relatório
- [ ] Analise: quais produtos dão mais lucro?
- [ ] Calcule margem média

---

## 🔗 Integração Automática

### Vendas Online (Mercado Pago)
```
✅ São contadas AUTOMATICAMENTE
✅ Aparecem no card "🌐 Vendas Online"
✅ Status deve ser "approved"
✅ Custo é calculado pelo cost_usd do produto
```

### Vendas Manuais
```
✅ Você registra manualmente
✅ Aparecem no card "🛒 Vendas Manuais"
✅ Histórico completo na tabela
✅ Pode editar/deletar quando quiser
```

### Recargas de Painel
```
✅ Você registra quando compra
✅ Aparece no card "📉 Custos Totais"
✅ Desconta do lucro automaticamente
✅ Histórico com cotação usada
```

---

## 📈 Visualização de Dados

Todos os números usam **formatação brasileira**:
- Milhares: `1.000,00` (ponto para milhares)
- Decimais: `5,50` (vírgula para decimal)
- Moeda: `R$ 1.000,00` ou `$ 50,00`

---

## 🚀 Próximas Melhorias Possíveis

- [ ] Gráficos de lucro por dia/semana/mês
- [ ] Exportar relatório em PDF
- [ ] Filtrar vendas por período
- [ ] Calcular ticket médio
- [ ] Alertas de lucro baixo
- [ ] Comparar lucro mês a mês

---

## ❓ FAQ

**P: Posso deletar uma venda depois de registrar?**  
R: Sim! Clique 🗑️ na tabela e ela será removida.

**P: Os dados são salvos automaticamente?**  
R: Sim! Quando você clica em "Registrar", é salvo no banco de dados.

**P: Posso acessar o histórico depois?**  
R: Sim! Sempre que voltar para a aba "Vendas & Lucros", você vê todo o histórico.

**P: Como é calculada a margem de lucro?**  
R: `(Lucro Total ÷ Faturamento Total) × 100`

**P: O IOF (6.38%) é descontado automaticamente?**  
R: Sim! Ao registrar recargas, o sistema multiplica por 1.0638.

---

## 📞 Suporte

Se encontrar problema:
1. Verifique se preencheu todos os campos obrigatórios
2. Clique em "🔄 Atualizar Relatório"
3. Se continuar, verifique o console (F12 > Console) para erros

Tudo está funcionando? Ótimo! 🎉
