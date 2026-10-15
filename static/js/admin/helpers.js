/* =========================
   HELPERS - Funções utilitárias
========================= */

function setVal(id, value) {
    const el = document.getElementById(id);
    if (!el) {
        console.warn(`Elemento #${id} não encontrado`);
        return;
    }

    if (el.type === 'checkbox') {
        el.checked = value == 1 || value === true;
    } else {
        el.value = value ?? '';
    }
}

function openModal(id) {
    const m = document.getElementById(id);
    if (m) {
        m.classList.remove('hidden');
        m.classList.add('flex');
        // Pequeno delay para animação se houver
        setTimeout(() => m.classList.add('modal-active'), 10);
    } else {
        console.error('Modal não encontrado:', id);
    }
}

function closeModal(id) {
    const m = document.getElementById(id);
    m?.classList.remove('modal-active');
    m?.classList.add('hidden');
    m?.classList.remove('flex');
}

function showSection(id) {
    // Esconde todas as seções
    document.querySelectorAll('.section-content').forEach(s => s.classList.add('hidden'));

    // Reseta abas
    document.querySelectorAll('[id^="tab-"]').forEach(t => {
        t.classList.remove('neon-cyan', 'border-b-2');
        t.classList.add('text-gray-400');
    });

    // Mostra a seção desejada
    const section = document.getElementById(`section-${id}`);
    if (section) {
        section.classList.remove('hidden');

        // CORREÇÃO: Força o AOS a recalcular posições
        if (typeof AOS !== 'undefined') {
            setTimeout(() => AOS.refresh(), 100);
        }
    }

    // Ativa aba
    const tab = document.getElementById(`tab-${id}`);
    tab?.classList.add('neon-cyan', 'border-b-2');
    tab?.classList.remove('text-gray-400');
}

function setupMobileMenu() {
    const btnMenu = document.getElementById('btn-menu-mobile');
    const menuPanel = document.getElementById('menu-mobile');
    const overlay = document.getElementById('menu-mobile-overlay');
    const btnClose = document.getElementById('btn-close-menu');

    function openMenu() {
        menuPanel?.classList.remove('translate-x-full');
        overlay?.classList.remove('hidden');
        document.body.style.overflow = 'hidden';
    }

    function closeMenu() {
        menuPanel?.classList.add('translate-x-full');
        overlay?.classList.add('hidden');
        document.body.style.overflow = '';
    }

    btnMenu?.addEventListener('click', openMenu);
    overlay?.addEventListener('click', closeMenu);
    btnClose?.addEventListener('click', closeMenu);

    document.querySelectorAll('.nav-mobile-link').forEach(l =>
        l.addEventListener('click', closeMenu)
    );
}

function updateCommissionInputs(prefix) {
    const typeSelect = document.getElementById(`${prefix}_commission_type`);
    const valWrapper = document.getElementById(`${prefix}_commission_val_wrapper`);
    const valInput = document.getElementById(`${prefix}_commission_value`);
    const prefixSpan = document.getElementById(`${prefix}_commission_val_prefix`);
    const suffixSpan = document.getElementById(`${prefix}_commission_val_suffix`);
    const paysCommInput = document.getElementById(`${prefix}_pays_commission`);
    const helpP = document.getElementById(`${prefix}_commission_help`);

    if (!typeSelect) return;
    const type = typeSelect.value;

    if (type === 'percent') {
        if (valWrapper) valWrapper.classList.remove('hidden');
        if (prefixSpan) prefixSpan.classList.add('hidden');
        if (suffixSpan) suffixSpan.classList.remove('hidden');
        if (valInput) valInput.placeholder = 'Ex: 15.00';
        if (paysCommInput) paysCommInput.value = '1';
        if (helpP) helpP.innerText = 'O vendedor receberá a porcentagem informada acima sobre o valor da venda deste produto.';
    } else if (type === 'fixed') {
        if (valWrapper) valWrapper.classList.remove('hidden');
        if (prefixSpan) prefixSpan.classList.remove('hidden');
        if (suffixSpan) suffixSpan.classList.add('hidden');
        if (valInput) valInput.placeholder = 'Ex: 10.00';
        if (paysCommInput) paysCommInput.value = '1';
        if (helpP) helpP.innerText = 'O vendedor receberá o valor fixo em R$ informado acima por cada unidade vendida.';
    } else if (type === 'none') {
        if (valWrapper) valWrapper.classList.add('hidden');
        if (paysCommInput) paysCommInput.value = '0';
        if (helpP) helpP.innerText = 'Nenhuma comissão será gerada para os vendedores nas vendas deste produto.';
    } else {
        // default
        if (valWrapper) valWrapper.classList.add('hidden');
        if (paysCommInput) paysCommInput.value = '1';
        if (helpP) helpP.innerText = 'O vendedor receberá a porcentagem padrão configurada no cupom dele (ex: 10%).';
    }
}

