# ⚡ Raio Mods Site

Painel de administração para gerenciamento de vendas manuais, produtos e links de downloads.

## 📋 Funcionalidades

- **Dashboard Financeiro**: Visão geral de lucro, vendas e custos.
- **Gestão de Produtos**: Adicionar, editar e remover produtos e catálogos.
- **Vendas Manuais**: Registrar vendas feitas fora do site automático, com cálculo de lucro.
- **Relatórios**: Histórico detalhado de vendas e recargas.
- **Links Dinâmicos**: Gerenciamento de links de download (Google Drive, Discord, etc).

## 🚀 Como Rodar Localmente

1. **Instale as dependências**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure as variáveis de ambiente**:
   Crie um arquivo `.env` na raiz (use `.env.example` como base):
   ```ini
   SECRET_KEY=sua_chave_secreta
   ADMIN_PASSWORD=sua_senha_admin
   ```

3. **Inicie o servidor**:
   ```bash
   python app.py
   ```
   O sistema verificará e criará o banco de dados `database.db` automaticamente.

4. **Acesse**:
   - Site: `http://localhost:5000`
   - Admin: `http://localhost:5000/admin`

## 🛠️ Tecnologias

- **Backend**: Flask (Python)
- **Banco de Dados**: SQLite
- **Frontend**: HTML5, TailwindCSS (via CDN), JavaScript Vanilla
- **Integrações**: Mercado Pago (preparado)

## 📂 Estrutura

- `app.py`: Entrada da aplicação.
- `routes/`: Rotas separadas (admin, public, payment).
- `database/`: Conexão e migrações manuais do SQLite.
- `static/`: Arquivos estáticos (CSS, JS, Imagens).
- `templates/`: Templates HTML (Jinja2).
