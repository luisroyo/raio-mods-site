# 💰 Dashboard Financeiro - Resumo de Implementação

## ✅ O que foi implementado

Seu sistema agora possui um **Dashboard Financeiro completo** que monitora em tempo real:

1. **Cotação USD-BRL** atualizada dinamicamente via API AwesomeAPI
2. **Faturamento Bruto** (soma de todas as vendas aprovadas em BRL)
3. **Custos Totais** (produtos importados + custo fixo do painel)
4. **Lucro Líquido** (com IOF de 6.38% incluído)

---

## 📋 Alterações por Arquivo

### 1. **site/update_tables.py** ✏️
Adicionada coluna `cost_usd` na tabela `products`:
```sql
ALTER TABLE products ADD COLUMN cost_usd REAL DEFAULT 0.0
```
- Armazena o custo original em dólares de cada produto
- Usado para cálculos de lucro real

---

### 2. **site/routes/admin.py** 🔧

#### a) Importação do `requests`:
```python
import requests
```

#### b) Nova função `get_dolar_hoje()`:
```python
def get_dolar_hoje():
    """
    Consulta a cotação atual do dólar em tempo real via API AwesomeAPI.
    Retorna o valor 'bid' (compra) como float.
    Em caso de erro, retorna valor padrão de segurança (5.50).
    """
    try:
        response = requests.get('https://economia.awesomeapi.com.br/last/USD-BRL', timeout=5)
        if response.status_code == 200:
            data = response.json()
            if 'USDBRL' in data:
                bid = float(data['USDBRL']['bid'])
                return bid
    except Exception as e:
        print(f"⚠️ Erro ao consultar dólar: {e}")
    
    # Valor padrão de segurança
    return 5.50
```

#### c) Cálculos na rota `/admin` (GET):
```python
# --- CÁLCULOS FINANCEIROS ---
dolar_hoje = get_dolar_hoje()
IOF = 1.0638  # 6.38%
CUSTO_FIXO_PAINEL_USD = 50.0

# Busca todas as vendas aprovadas com join para pegar cost_usd
approved_orders = conn.execute('''
    SELECT o.*, p.cost_usd, p.price
    FROM orders o
    JOIN products p ON o.product_id = p.id
    WHERE o.status = 'approved'
''').fetchall()

faturamento_total = 0.0
custo_vendas_total = 0.0

for order in approved_orders:
    # Faturamento em BRL
    try:
        amount = float(str(order['amount']).replace('R$', '').replace(',', '.').strip())
        faturamento_total += amount
    except:
        pass
    
    # Custo das vendas em BRL (USD * cotação * IOF)
    try:
        cost_usd = float(order['cost_usd'] or 0)
        if cost_usd > 0:
            custo_vendas_total += (cost_usd * dolar_hoje * IOF)
    except:
        pass

# Custo fixo do painel (50 USD * cotação * IOF)
custo_fixo_painel_brl = CUSTO_FIXO_PAINEL_USD * dolar_hoje * IOF

# Lucro líquido final
lucro_liquido = faturamento_total - custo_vendas_total - custo_fixo_painel_brl

financeiro = {
    'dolar_hoje': round(dolar_hoje, 2),
    'faturamento_total': round(faturamento_total, 2),
    'custo_vendas_total': round(custo_vendas_total, 2),
    'custo_fixo_painel_brl': round(custo_fixo_painel_brl, 2),
    'lucro_liquido': round(lucro_liquido, 2),
    'total_vendas': len(approved_orders),
    'iof': IOF,
}
```

#### d) Adicionar `cost_usd` no formulário de adicionar produto:
Na função `add_product()`, adicione:
```python
# Novo: Recebe cost_usd
try:
    cost_usd = float(request.form.get('cost_usd', 0) or 0)
except:
    cost_usd = 0.0

# E atualize o INSERT:
conn.execute('INSERT INTO products (..., cost_usd) VALUES (..., ?)',
             (..., cost_usd))
```

#### e) Adicionar `cost_usd` no formulário de editar produto:
Na função `edit_product()`, adicione:
```python
# Novo: Recebe cost_usd
try:
    cost_usd = float(request.form.get('cost_usd') or existing.get('cost_usd', 0) or 0)
except:
    cost_usd = float(existing.get('cost_usd', 0) or 0)

# E atualize o UPDATE:
conn.execute('UPDATE products SET ..., cost_usd=? WHERE id=?',
             (..., cost_usd, pid))
```

#### f) Passar `financeiro` para o template:
```python
return render_template('admin.html', ..., financeiro=financeiro)
```

---

### 3. **site/templates/admin.html** 🎨

#### a) Dashboard Financeiro (no topo de `<main>`):
```html
<!-- Dashboard Financeiro -->
<div class="mb-8 border-2 border-yellow-500 rounded-lg p-6 bg-yellow-500/5">
    <h2 class="text-2xl font-bold text-yellow-500 mb-6">💰 Dashboard Financeiro</h2>
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <!-- Cotação Atual -->
        <div class="border border-blue-500 rounded-lg p-4 bg-black/50">
            <p class="text-xs text-gray-400 mb-2">📊 Cotação USD-BRL</p>
            <p class="text-3xl font-bold text-blue-500">{{ financeiro.dolar_hoje }}</p>
            <p class="text-xs text-gray-500 mt-1">Atualizado em tempo real</p>
        </div>
        
        <!-- Faturamento Bruto -->
        <div class="border border-green-500 rounded-lg p-4 bg-black/50">
            <p class="text-xs text-gray-400 mb-2">💵 Faturamento Bruto</p>
            <p class="text-3xl font-bold text-green-500">R$ {{ "{:,.2f}".format(financeiro.faturamento_total) }}</p>
            <p class="text-xs text-gray-500 mt-1">{{ financeiro.total_vendas }} vendas aprovadas</p>
        </div>
        
        <!-- Custos Totais -->
        <div class="border border-red-500 rounded-lg p-4 bg-black/50">
            <p class="text-xs text-gray-400 mb-2">📉 Custos Totais</p>
            <p class="text-3xl font-bold text-red-500">R$ {{ "{:,.2f}".format(financeiro.custo_vendas_total + financeiro.custo_fixo_painel_brl) }}</p>
            <p class="text-xs text-gray-500 mt-1">Produtos + Painel ($50 USD)</p>
        </div>
        
        <!-- Lucro Líquido -->
        <div class="border {% if financeiro.lucro_liquido >= 0 %}border-green-500{% else %}border-red-500{% endif %} rounded-lg p-4 bg-black/50">
            <p class="text-xs text-gray-400 mb-2">🎯 Lucro Líquido</p>
            <p class="text-3xl font-bold {% if financeiro.lucro_liquido >= 0 %}text-green-500{% else %}text-red-500{% endif %}">R$ {{ "{:,.2f}".format(financeiro.lucro_liquido) }}</p>
            <p class="text-xs text-gray-500 mt-1">IOF: {{ (financeiro.iof * 100)|int }}% (6.38%)</p>
        </div>
    </div>
    <details class="mt-4 p-3 bg-gray-900/50 rounded text-xs text-gray-400 border border-gray-700">
        <summary class="cursor-pointer font-bold text-gray-300">📋 Detalhes dos Cálculos</summary>
        <div class="mt-3 space-y-2">
            <p>💰 Faturamento Bruto: R$ {{ "{:,.2f}".format(financeiro.faturamento_total) }}</p>
            <p>📦 Custo de Produtos: R$ {{ "{:,.2f}".format(financeiro.custo_vendas_total) }} (Compra em USD + IOF)</p>
            <p>🏪 Custo Painel Fixo: R$ {{ "{:,.2f}".format(financeiro.custo_fixo_painel_brl) }} ($50 USD × {{ financeiro.dolar_hoje }} × {{ financeiro.iof }})</p>
            <p>✅ Lucro Líquido: R$ {{ "{:,.2f}".format(financeiro.lucro_liquido) }}</p>
        </div>
    </details>
</div>
```

#### b) Campo `cost_usd` em "Novo Produto Solto":
```html
<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
    <input type="number" name="cost_usd" step="0.01" placeholder="Custo (USD)" 
           class="w-full px-4 py-2 bg-black border border-purple-500 rounded text-white" 
           title="Quanto você paga pelo produto em dólares">
    <input type="text" name="payment_url" placeholder="Link Mercado Pago (Opcional se usar automático)" 
           class="w-full px-4 py-2 bg-black border border-green-500 rounded text-white">
</div>
```

#### c) Campo `cost_usd` no modal de edição:
```html
<div>
    <label class="text-xs text-gray-400 block mb-1">💸 Custo em USD (para cálculos)</label>
    <input type="number" id="edit_cost_usd" name="cost_usd" step="0.01" 
           class="w-full p-2 bg-gray-900 border border-purple-500 rounded text-white" 
           placeholder="Ex: 9.99" 
           title="Quanto você paga pelo produto em dólares">
</div>
```

#### d) Campo `cost_usd` no modal de adicionar subproduto:
```html
<div class="grid grid-cols-2 gap-2">
    <input type="text" name="category" required placeholder="Categoria (ex: Key)" 
           class="w-full p-2 bg-gray-900 border border-green-500 rounded text-white">
    <input type="number" name="cost_usd" step="0.01" placeholder="Custo USD" 
           class="w-full p-2 bg-gray-900 border border-purple-500 rounded text-white" 
           title="Quanto você paga pelo produto em dólares">
</div>
```

#### e) Adicionar `cost_usd` nas chamadas `openEditModal()`:
```html
<!-- Catálogo -->
<button type="button" onclick='openEditModal(..., {{ (catalog.cost_usd|default(0))|tojson|forceescape }})'>

<!-- Subproduto -->
<button type="button" onclick='openEditModal(..., {{ (sub.cost_usd|default(0))|tojson|forceescape }})'>

<!-- Produto Solto -->
<button type="button" onclick='openEditModal(..., {{ (prod.cost_usd|default(0))|tojson|forceescape }})'>
```

---

### 4. **site/static/js/admin.js** 📝

Atualizar função `openEditModal()`:
```javascript
function openEditModal(
    id, name, desc, price, cat, img,
    tagline, sort, pid, isCat,
    payUrl, promoPrice, promoLabel, costUsd
) {
    setVal('edit_id', id);
    setVal('edit_name', name);
    setVal('edit_description', desc);
    setVal('edit_price', price);
    setVal('edit_category', cat);
    setVal('edit_tagline', tagline);
    setVal('edit_sort_order', sort || 0);
    setVal('edit_is_catalog', isCat);
    setVal('edit_payment_url', payUrl);
    setVal('edit_promo_price', promoPrice);
    setVal('edit_promo_label', promoLabel);
    setVal('edit_cost_usd', costUsd || 0);
    setVal('edit_image_url', '');
    // ... resto da função
}
```

---

## 📐 Fórmulas Utilizadas

### Faturamento Total
```
Faturamento Total = Σ (Valor de cada venda aprovada em BRL)
```

### Custo das Vendas
```
Custo Vendas = Σ (cost_usd × Cotação USD-BRL × IOF)
onde IOF = 1.0638 (6.38%)
```

### Custo Fixo do Painel
```
Custo Fixo Painel = $50 USD × Cotação USD-BRL × IOF
```

### Lucro Líquido
```
Lucro Líquido = Faturamento Total - Custo Vendas - Custo Fixo Painel
```

---

## 🚀 Como Usar

### Passo 1: Adicionar Custo ao Criar um Produto
Ao criar um produto novo (solto, em um jogo ou subproduto), preencha:
- **Nome**: Nome do produto
- **Preço**: Valor em BRL que você vende
- **Custo (USD)**: O quanto você paga em dólares (novo campo)

### Passo 2: Ver Dashboard em Tempo Real
Acesse `/admin` e você verá:
- 📊 Cotação USD atualizada (consultada via API)
- 💵 Total faturado (vendas aprovadas)
- 📉 Total de custos (produtos + painel)
- 🎯 Seu lucro líquido (verde se positivo, vermelho se negativo)

### Passo 3: Clicar em "Detalhes dos Cálculos"
Há uma seção expansível que mostra exatamente como cada valor foi calculado.

---

## ⚙️ Configurações Importantes

- **API de Cotação**: `https://economia.awesomeapi.com.br/last/USD-BRL`
- **IOF Padrão**: 6.38% (1.0638)
- **Custo Fixo Painel**: $50 USD (configurável em `get_dolar_hoje()`)
- **Timeout API**: 5 segundos
- **Valor Padrão Dólar**: R$ 5.50 (se API falhar)

---

## 🔒 Segurança & Tratamento de Erros

✅ Try/except na API de cotação (retorna valor padrão se falhar)  
✅ Validação de valores de custo (converte para float, padrão 0)  
✅ Join seguro com tabela orders (usa SQL parametrizado)  
✅ Formatação de strings de preço (remove R$, converte)  

---

## 📊 Exemplo de Dados

Se você tiver:
- **Cotação**: R$ 5,20
- **Vendas**: R$ 1.000,00 (10 vendas)
- **Custo Produto**: $100 USD
- **Custo Painel**: $50 USD

Então:
```
Faturamento:    R$ 1.000,00
Custo Vendas:   $100 × 5,20 × 1,0638 = R$ 553,18
Custo Painel:   $50 × 5,20 × 1,0638 = R$ 276,59
─────────────────────────────────────
Lucro Líquido:  R$ 1.000,00 - 553,18 - 276,59 = R$ 170,23 ✅
```

---

## 🐛 Troubleshooting

**P: O dashboard mostra cotação padrão (5.50)?**  
R: A API pode estar indisponível. Verifique sua conexão de internet e o timeout.

**P: Os cálculos parecem errados?**  
R: Verifique se todos os seus produtos têm `cost_usd` preenchido no banco.

**P: Onde vejo vendas que não estão "approved"?**  
R: O dashboard só conta vendas com status `'approved'`. Verifique a tabela `orders`.

---

## 📝 Próximos Passos (Sugestões)

- [ ] Adicionar gráficos de lucro por dia/mês
- [ ] Exportar relatório financeiro em PDF
- [ ] Alertas se lucro fica negativo
- [ ] Previsão de lucro baseado em vendas históricas
- [ ] Integração com contabilidade

---

## ✅ Status de Implementação

- ✅ Banco de dados (coluna `cost_usd`)
- ✅ Backend (cálculos e API)
- ✅ Frontend (Dashboard visual)
- ✅ Formulários (campos de entrada)
- ✅ Commit e Deploy (PythonAnywhere)

**Tudo pronto para usar! 🎉**
