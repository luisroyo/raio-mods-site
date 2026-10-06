# Tarefas Pendentes (TODO)

## Segurança (Segurança e OWASP ZAP)

- [ ] **Implementar Proteção Anti-CSRF (Cross-Site Request Forgery):**
  - **Contexto:** Um scan do OWASP ZAP apontou a "Ausência de tokens Anti-CSRF". Atualmente, a aplicação usa `SameSite=Lax` nos cookies de sessão (configurado no `app.py`), o que mitiga grande parte dos riscos de CSRF nos navegadores modernos. No entanto, a implementação de tokens em todos os formulários é a prática recomendada.
  - **Ação Necessária:** 
    1. Instalar a biblioteca `Flask-WTF` (`pip install Flask-WTF`).
    2. Inicializar o `CSRFProtect(app)` no arquivo `app.py`.
    3. Adicionar a tag `{{ csrf_token() }}` em **todos** os formulários HTML (`<form>`) localizados na pasta `templates/` (aproximadamente 30 formulários).
    4. Garantir que as requisições AJAX (JavaScript) também enviem o token CSRF no cabeçalho (ex: `X-CSRFToken`).
  - **Prioridade:** Média/Baixa (devido à mitigação já feita com o `SameSite=Lax`). Fazer em uma futura atualização com calma para poder testar todos os formulários e garantir que nada quebrou.
