# 📸 Guia Visual do Sistema de Vendas

## Layout da Nova Aba "💰 Vendas & Lucros"

### Seção 1: Resumo em Cards

```
╔════════════════════════════════════════════════════════════════════════════╗
║  📊 Resumo de Vendas (Em Tempo Real)          [🔄 Atualizar Relatório]    ║
╠════════════════════════════════════════════════════════════════════════════╣
║                                                                            ║
║  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐        ║
║  │ 🌐 Vendas Online │  │ 🛒 Vendas Manual │  │ 💰 Faturamento   │        ║
║  │                  │  │                  │  │                  │        ║
║  │ R$ 1.234,56      │  │ R$ 567,89        │  │ R$ 1.802,45      │        ║
║  │ (5 vendas)       │  │ (12 vendas)      │  │ (17 vendas)      │        ║
║  └──────────────────┘  └──────────────────┘  └──────────────────┘        ║
║                                                                            ║
║  ┌──────────────────┐  ┌──────────────────┐                               ║
║  │ 📉 Custos Totais │  │ 🎯 Lucro Total   │                               ║
║  │                  │  │                  │                               ║
║  │ R$ 892,30        │  │ R$ 910,15        │                               ║
║  │ Produtos + Painel│  │ IOF: 6.38%       │                               ║
║  └──────────────────┘  └──────────────────┘                               ║
║                                                                            ║
╚════════════════════════════════════════════════════════════════════════════╝
```

### Seção 2: Registrar Venda Manual

```
╔════════════════════════════════════════════════════════════════════════════╗
║  🛒 Registrar Venda Manual                                                 ║
╠════════════════════════════════════════════════════════════════════════════╣
║                                                                            ║
║  Produto: [▼ Selecione um Produto                    ]                    ║
║           ├─ KOS Virtual - 30 Dias                                        ║
║           ├─ Premium Key - 1 Mês                                          ║
║           ├─ 📁 Jogos Variados                                            ║
║           │  ├─ GTA V - Standard                                          ║
║           │  └─ GTA V - Premium                                           ║
║                                                                            ║
║  Quantidade:     [1                               ]                       ║
║                                                                            ║
║  Preço de Venda: [R$ 50,00                        ]                       ║
║                  Quanto o cliente pagou                                    ║
║                                                                            ║
║  Custo Unitário: [R$ 15,00                        ]                       ║
║                  Quanto você pagou                                         ║
║                                                                            ║
║  Notas:          [Venda pelo WhatsApp              ]                       ║
║                                                                            ║
║                     [💾 Registrar Venda Manual]                            ║
║                                                                            ║
╚════════════════════════════════════════════════════════════════════════════╝
```

### Seção 3: Registrar Recarga de Painel

```
╔════════════════════════════════════════════════════════════════════════════╗
║  🔄 Recarga de Painel                                                      ║
╠════════════════════════════════════════════════════════════════════════════╣
║                                                                            ║
║  Quantidade de Painéis: [20                      ]                        ║
║                                                                            ║
║  Custo Unitário (USD):  [50.00                   ]                        ║
║                                                                            ║
║  Cotação USD-BRL:       [5.20                    ]                        ║
║                         (auto-preenchida com valor atual)                 ║
║                                                                            ║
║  Notas:                 [Fornecedor ABC, Lote 12345 ]                     ║
║                                                                            ║
║                     [📦 Registrar Recarga]                                 ║
║                                                                            ║
╚════════════════════════════════════════════════════════════════════════════╝
```

### Seção 4: Histórico de Vendas Manuais

```
╔════════════════════════════════════════════════════════════════════════════╗
║  📋 Histórico de Vendas Manuais                                            ║
╠════════════════════════════════════════════════════════════════════════════╣
║                                                                            ║
║  ┌──────────────────┬──────┬──────────┬──────────┬────────────┬────────┐ ║
║  │ Produto          │ Qtd  │ P.Venda  │ Custo    │ Total Vnd  │ Lucro  │ ║
║  ├──────────────────┼──────┼──────────┼──────────┼────────────┼────────┤ ║
║  │ KOS Virtual      │  2   │ R$ 50    │ R$ 15    │ R$ 100,00  │ R$ 70  │ ║
║  │ Premium Key      │  1   │ R$ 30    │ R$ 8     │ R$ 30,00   │ R$ 22  │ ║
║  │ GTA V Standard   │  3   │ R$ 25    │ R$ 12    │ R$ 75,00   │ R$ 39  │ ║
║  ├──────────────────┼──────┼──────────┼──────────┼────────────┼────────┤ ║
║  │                  │      │          │   TOTAL  │ R$ 205,00  │R$ 131  │ ║
║  └──────────────────┴──────┴──────────┴──────────┴────────────┴────────┘ ║
║                                                                            ║
║  [Data: 05/02/2026  10:30] [Data: 04/02/2026  14:15] [Data: 03/02/2026] ║
║  [🗑️ Deletar]              [🗑️ Deletar]              [🗑️ Deletar]      ║
║                                                                            ║
╚════════════════════════════════════════════════════════════════════════════╝
```

### Seção 5: Histórico de Recargas

```
╔════════════════════════════════════════════════════════════════════════════╗
║  📦 Histórico de Recargas de Painel                                        ║
╠════════════════════════════════════════════════════════════════════════════╣
║                                                                            ║
║  ┌─────┬─────────────┬──────────┬──────────┬──────────┬──────────────────┐║
║  │ Qtd │ Custo Unit  │ Total    │ Cotação  │ Total    │ Notas            ││
║  │     │ (USD)       │ (USD)    │          │ (BRL)    │                  ││
║  ├─────┼─────────────┼──────────┼──────────┼──────────┼──────────────────┤║
║  │ 20  │ $50,00      │ $1000    │ R$ 5,20  │ R$ 5.319 │ Fornecedor ABC  ││
║  │ 10  │ $48,00      │ $480     │ R$ 5,15  │ R$ 2.505 │ Lote 12345      ││
║  │ 15  │ $52,00      │ $780     │ R$ 5,25  │ R$ 4.306 │ Emergencial     ││
║  └─────┴─────────────┴──────────┴──────────┴──────────┴──────────────────┘║
║                                                                            ║
║  [Data: 05/02/2026] [🗑️] [Data: 03/02/2026] [🗑️] [Data: 02/02/2026] [🗑️]║
║                                                                            ║
╚════════════════════════════════════════════════════════════════════════════╝
```

---

## Fluxo de Uso (Passo a Passo)

### 1. Acessar o Painel

```
1. Entre em seu site admin
2. Clique na aba: [📂 Jogos] [🛍️ Produtos] [💰 Vendas & Lucros] [🔗 Links]
3. Você está na seção de vendas!
```

### 2. Registrar Uma Venda Manual

```
Cenário: Você vendeu 2 licenças por WhatsApp

1. Scroll para "🛒 Registrar Venda Manual"
2. Selecione: KOS Virtual - 30 Dias
3. Digite Quantidade: 2
4. Digite Preço de Venda: R$ 50,00 (por unidade)
5. Digite Custo Unitário: R$ 15,00 (por unidade)
6. Digite Notas: "Cliente João - WhatsApp"
7. Clique: [💾 Registrar Venda Manual]
8. Mensagem verde: "✅ Venda manual registrada!"
9. Vê na tabela abaixo: Total = R$ 100,00 | Lucro = R$ 70,00
```

### 3. Registrar Uma Recarga

```
Cenário: Você comprou 20 painéis em dólares

1. Scroll para "🔄 Recarga de Painel"
2. Digite Quantidade: 20
3. Digite Custo Unitário: 50.00 (em USD)
4. Cotação já vem preenchida com a atual
5. Digite Notas: "Fornecedor ABC"
6. Clique: [📦 Registrar Recarga]
7. Mensagem verde: "✅ Recarga de painel registrada!"
8. Vê na tabela: $1000 USD = R$ 5.319 BRL (com IOF)
```

### 4. Atualizar Relatório

```
1. Clique em: [🔄 Atualizar Relatório]
2. Sistema recalcula tudo automaticamente
3. Cards no topo mostram:
   - Total Online (automático)
   - Total Manual (que você registrou)
   - Total de Custos
   - Lucro Final (verde se positivo!)
```

---

## Cores e Significados

| Cor | Significado | Exemplo |
|-----|-------------|---------|
| 🔵 Azul | Vendas Online | Mercado Pago |
| 🟣 Roxo | Vendas Manuais | Registros offline |
| 🟠 Laranja | Recargas | Painéis importados |
| 🟢 Verde | Lucro/Positivo | R$ 1.234,56 ✅ |
| 🔴 Vermelho | Custo/Negativo | -R$ 567,89 ❌ |
| 🟡 Amarelo | Lucro Detalhado | Nas tabelas |

---

## Exemplos de Cálculos

### Exemplo 1: Venda Simples
```
Você registra:
- Produto: KOS Virtual
- Quantidade: 1
- Preço de Venda: R$ 50,00
- Custo Unitário: R$ 15,00
- Notas: Cliente do WhatsApp

Sistema calcula:
- Total Venda: 1 × R$ 50 = R$ 50,00
- Total Custo: 1 × R$ 15 = R$ 15,00
- Lucro: R$ 50 - R$ 15 = R$ 35,00 ✅
```

### Exemplo 2: Venda em Lote
```
Você registra:
- Produto: Premium Key
- Quantidade: 5
- Preço de Venda: R$ 30,00
- Custo Unitário: R$ 8,00

Sistema calcula:
- Total Venda: 5 × R$ 30 = R$ 150,00
- Total Custo: 5 × R$ 8 = R$ 40,00
- Lucro: R$ 150 - R$ 40 = R$ 110,00 ✅
```

### Exemplo 3: Recarga com IOF
```
Você registra:
- Quantidade: 20 painéis
- Custo Unitário: $50 USD
- Cotação: R$ 5,20

Sistema calcula:
- Total USD: 20 × $50 = $1.000 USD
- Com IOF 6.38%: $1.000 × 1.0638 = R$ 5.532,00
- Nota: Nesse mês vai deduzir R$ 5.532 do seu lucro
```

---

## Mensagens e Feedback

### ✅ Sucesso
```
Verde: "✅ Venda manual registrada!"
Verde: "✅ Recarga de painel registrada!"
```

### ❌ Erro
```
Vermelho: "❌ Dados inválidos"
Vermelho: "❌ Todos os campos são obrigatórios"
Vermelho: "❌ Erro ao excluir"
```

### ⚠️ Confirmações
```
"Excluir esta venda?" → Clique [OK] para confirmar
"Excluir esta recarga?" → Clique [OK] para confirmar
```

---

## Dicas de Uso

### ✅ Faça Assim
- [ ] Registre vendas **no mesmo dia**
- [ ] Use **cotação correta** nas recargas
- [ ] Coloque **notas descritivas**
- [ ] Clique "Atualizar" **regularmente**
- [ ] Revise o **histórico semanalmente**

### ❌ Evite Isto
- [ ] Não registre vendas antigas
- [ ] Não use cotação de dias passados
- [ ] Não deixe campos em branco
- [ ] Não delete dados sem backup
- [ ] Não esqueça de atualizar o relatório

---

## Responsividade

### Desktop (Tela Grande)
```
┌─ Tabelas lado a lado
├─ Formulários em 2 colunas
├─ Todos os cards visíveis
└─ Layout expandido
```

### Tablet (Tela Média)
```
┌─ Tabelas com scroll horizontal
├─ Formulários em 2 colunas
├─ Cards empilhados
└─ Parcialmente adaptado
```

### Mobile (Tela Pequena)
```
┌─ Tabelas com scroll horizontal
├─ Formulários em 1 coluna
├─ Cards em fila
└─ Totalmente mobile-friendly
```

---

## Atalhos Rápidos

| Ação | Comando |
|------|---------|
| Ir para "Vendas & Lucros" | `/admin` → Aba 3 |
| Registrar venda | Preencha + Clique |
| Registrar recarga | Preencha + Clique |
| Deletar | Clique 🗑️ |
| Atualizar | Clique 🔄 |
| Ver detalhes | Hover nos cards |

---

## Checklist Diário

Você pode usar como template:

```
[ ] ☀️ Manhã
    [ ] Verificar painel
    [ ] Atualizar relatório
    
[ ] 🌅 Dia
    [ ] Registrar vendas do site
    [ ] Registrar vendas manuais
    
[ ] 🌙 Noite
    [ ] Conferir números
    [ ] Registrar recargas (se houver)
    [ ] Clique em "Atualizar"
```

---

Tudo pronto! Seu sistema está 100% visual e intuitivo. Bora lucrar! 💰✨
