# ⚡ Raio Mods - E-commerce de Produtos Digitais

Plataforma completa para venda automática de chaves (keys), contas e produtos digitais, com integração Pix (Mercado Pago), painel administrativo robusto e otimização para SEO.

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-3.0-green.svg)
![TailwindCSS](https://img.shields.io/badge/TailwindCSS-3.0-informational.svg)
![SQLite](https://img.shields.io/badge/Database-SQLite-lightgrey.svg)

## � Funcionalidades Principais

### 🛒 Loja & Catálogo
- **Venda de Produtos Digitais**: Entrega automática de chaves (keys) após pagamento.
- **Catálogo Dinâmico**: Suporte a produtos simples e catálogos (agrupamento de produtos).
- **Busca Inteligente**: Pesquisa por nome e categoria.
- **SEO Dinâmico**: Meta tags (Open Graph) automáticas para compartilhamento bonito no WhatsApp/Telegram.
- **Performance**: Imagens com carregamento lento (`lazy loading`) e otimização WebP.

### 💰 Pagamentos & Financeiro
- **Integração Mercado Pago**: 
    - Pix Automático (QR Code Copy & Paste).
    - Cartão de Crédito (Checkout Transparente).
- **Cotação Dólar**: Atualização automática da taxa de câmbio (com cache de 10min) para precificação de custos.
- **Dashboard Financeiro**: 
    - Visão geral de lucro, faturamento e custos.
    - Gráficos e indicadores de performance.

### 🛡️ Administração & Segurança
- **Painel Admin Completo**: 
    - Gerenciamento de Produtos (Adicionar, Editar, Ocultar/Exibir).
    - Gerenciamento de Estoque de Chaves.
    - Gerenciamento de Links Utéis.
- **Segurança Reforçada**: Auditoria automática de senhas fracas.
- **Backup**: Download do banco de dados (`database.db`) direto pelo painel.

---

## 🛠️ Tecnologias Utilizadas

- **Backend**: Python (Flask)
- **Frontend**: HTML5, JavaScript (Vanilla), Tailwind CSS
- **Banco de Dados**: SQLite
- **Pagamentos**: SDK Mercado Pago
- **Imagens**: Pillow (Processamento e Otimização)

---

## ⚙️ Instalação e Configuração

### 1. Requisitos
- Python 3.10 ou superior
- Conta no Mercado Pago (para credenciais de API)

### 2. Instalação
Clone o repositório e instale as dependências:

```bash
git clone https://github.com/seu-usuario/raio-mods-site.git
cd raio-mods-site
pip install -r requirements.txt
```

### 3. Configuração (.env)
Crie um arquivo `.env` na raiz do projeto com as suas configurações:

```env
SECRET_KEY=sua_chave_secreta_super_segura
ADMIN_PASSWORD=sua_senha_admin
```

> **Nota**: O Token do Mercado Pago e outras configs são gerenciados direto pelo Painel Admin no banco de dados.

### 4. Executando
```bash
python app.py
```
O site estará acessível em `http://localhost:5000`.

---

## � Segurança em Produção (Deploy)

Para rodar em produção (ex: PythonAnywhere, VPS):
1.  Garanta que o `SECRET_KEY` e `ADMIN_PASSWORD` no `.env` sejam fortes.
2.  O sistema alertará no Dashboard se detectar configurações padrão inseguras.
3.  Utilize um servidor WSGI (Gunicorn, uWSGI) ou a configuração padrão do seu host.

---

## 📜 Licença
Este projeto é de uso privado/proprietário.
