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
