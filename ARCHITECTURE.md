# Arquitetura do Sistema - RAIO MODS

Este documento serve como a fonte da verdade da arquitetura do sistema do site e bot da **RAIO MODS**, contendo as definições dos fluxos de pagamentos, integração com o Telegram, internacionalização e banco de dados.

---

## 1. Integração de Pagamento Automatizado (Telegram WebApp)

O sistema de checkout é unificado para o site e para o Bot do Telegram. A abertura ocorre por meio de uma janela overlay nativa (Telegram WebApp) sem redirecionamento para navegadores externos.

### Fluxo de Sequência Segura:
1. **Abertura**: O cliente clica no botão "Comprar" no Bot. O bot abre `/pagamento` injetando o SDK do Telegram.
2. **Autenticação**: O frontend (`telegram_webapp.js`) captura o `window.Telegram.WebApp.initData` e o anexa de forma invisível nas requisições POST para `/api/checkout`.
3. **Validação Criptográfica**: O backend intercepta o payload e o valida em `telegram_app/utils/auth.py` utilizando o algoritmo oficial do Telegram (HMAC-SHA256 com o token do Bot).
4. **Tolerância a Falhas**: Caso o `initData` falhe na validação ou esteja ausente (compra comum no navegador), o checkout prossegue normalmente sem associar o Telegram ao pedido.
5. **Auditoria e Entrega**: Após confirmação do pagamento, a entrega é executada de forma assíncrona/não-bloqueante (`run_coroutine_threadsafe`) enviando a chave no chat privado e atualizando as colunas de auditoria na tabela `orders`:
   - `telegram_id`, `telegram_username`, `telegram_first_name`
   - `telegram_delivery_status` (`'delivered'` ou `'failed'`)
   - `telegram_delivered_at` (gravação via `CURRENT_TIMESTAMP` do banco)
   - `telegram_message_id` (ID da mensagem de entrega do Telegram)
   - `telegram_delivery_error` (motivo do erro se o envio falhar)

---

## 2. Internacionalização (i18n) & Localização

O sistema é preparado para múltiplos idiomas (Português, Inglês e Espanhol) e moedas (Real - BRL e Dólar - USD).

### Regras de Ouro:
* **Sem Tradução Automática**: Proibido utilizar APIs de tradução automática em tempo de execução. Traduções de catálogo ficam salvas no banco de dados e as de interface em JSON local, eliminando latências e dependências de terceiros.
* **Fallback de Idioma por Campo**: Se um campo de tradução (inglês/espanhol) estiver vazio no banco, o sistema exibe a versão correspondente em português para aquele campo específico (ex: `name_en` se preenchido é exibido, mas se `description_en` for vazio usa `description_pt`), permitindo traduções parciais de forma limpa.

### Estrutura de Banco de Dados de Produtos:
A tabela `products` possui suporte estruturado para múltiplos idiomas, moedas e controle de tradução:
- `name_pt` (TEXT), `name_en` (TEXT), `name_es` (TEXT)
- `description_pt` (TEXT), `description_en` (TEXT), `description_es` (TEXT)
- `price_brl` (DECIMAL(10,2)), `price_usd` (DECIMAL(10,2))
- `default_currency` (TEXT DEFAULT `'BRL'` - aceita estritamente `'BRL'` ou `'USD'`)
- `translation_status` (TEXT DEFAULT `'draft'` - indica progresso: `'draft'`, `'partial'`, `'complete'`)
- As colunas legadas (`name`, `description`, `price`) são mantidas por compatibilidade e facilidade de rollback.

### Detecção de Idioma do Usuário (Ordem de Prioridade):
1. Seleção manual explícita (URL query / ação do usuário).
2. Cookie de preferência.
3. Sessão do Flask.
4. Cabeçalho HTTP `Accept-Language` do navegador.
5. Fallback padrão: **Português (`pt-BR`)**.

### Moeda e Gateways de Pagamento Dinâmicos:
O sistema decide qual moeda exibir com base na localidade padrão do idioma selecionado (PT -> BRL, EN/ES -> USD), permitindo alteração manual. Os gateways são exibidos condicionalmente no checkout:
* Se moeda for **BRL**: Mostrar Pix e Cartão (Mercado Pago).
* Se moeda for **USD**: Mostrar Binance Pay (Cripto USDT).

### Localização no Bot do Telegram:
O bot lê a propriedade `language_code` enviada pelo aplicativo do usuário. Caso o idioma correspondente não esteja disponível, adota o **Inglês (`en`)** como fallback para a interface do Bot.
