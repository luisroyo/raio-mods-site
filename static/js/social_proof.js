const socialProofData = {
    names: [
        'João S.', 'Marcos P.', 'Lucas M.', 'Pedro H.', 'Gabriel F.', 
        'Felipe R.', 'Matheus T.', 'Gustavo B.', 'Ana C.', 'Carlos E.',
        'Thiago V.', 'Rafael L.', 'Bruno K.', 'Fernando D.', 'Diego A.'
    ],
    products: [
        'KOS VIRTUAL PREMIUM - 1 DIA', 'KOS VIRTUAL PREMIUM - 7 DIAS', 
        'KOS VIRTUAL PREMIUM - 15 DIAS', 'KOS VIRTUAL PREMIUM - 30 DIAS',
        'KOS APKMOD - 1 DIA', 'KOS APKMOD - 7 DIAS', 
        'KOS APKMOD - 15 DIAS', 'KOS APKMOD - 30 DIAS',
        'NINJA EXTERNAL - 3 DIAS', 'NINJA EXTERNAL - 7 DIAS', 'NINJA EXTERNAL - 30 DIAS',
        'AIMKIN - 3 DIAS', 'AIMKIN - 7 DIAS'
    ],
    times: [
        'agora mesmo', 'há 2 minutos', 'há 5 minutos', 'há 10 minutos',
        'há 15 minutos', 'há 30 minutos', 'há 1 hora'
    ]
};

function getRandomItem(array) {
    return array[Math.floor(Math.random() * array.length)];
}

function createSocialProofToast() {
    const container = document.getElementById('social-proof-container');
    if (!container) return;

    // Se já tiver um toast visível, não mostra outro
    if (container.children.length > 0) return;

    const name = getRandomItem(socialProofData.names);
    const product = getRandomItem(socialProofData.products);
    const time = getRandomItem(socialProofData.times);

    const toast = document.createElement('div');
    toast.style.transition = 'all 0.5s ease-in-out';
    toast.style.transform = 'translateY(40px)';
    toast.style.opacity = '0';
    toast.className = `bg-black/80 backdrop-blur-md border border-white/10 rounded-lg p-3 flex items-center gap-3 pointer-events-auto shadow-lg`;

    toast.innerHTML = `
        <div class="flex-shrink-0 w-10 h-10 rounded-full bg-gradient-to-br from-neon-cyan to-blue-600 flex items-center justify-center border border-white/20">
            <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z" />
            </svg>
        </div>
        <div class="flex flex-col">
            <div class="text-xs text-gray-300">
                <strong class="text-white">${name}</strong> comprou
            </div>
            <div class="text-sm font-bold text-neon-cyan leading-tight">
                ${product}
            </div>
            <div class="text-[10px] text-gray-500 mt-0.5">
                ${time}
            </div>
        </div>
        <button class="absolute top-2 right-2 text-gray-500 hover:text-white transition-colors" onclick="this.closest('div.transform').remove()">
            <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
            </svg>
        </button>
    `;

    container.appendChild(toast);

    // Fade in
    requestAnimationFrame(() => {
        setTimeout(() => {
            toast.style.transform = 'translateY(0)';
            toast.style.opacity = '1';
        }, 50);
    });

    // Fade out e remove após 5 segundos
    setTimeout(() => {
        if (toast.parentNode) {
            toast.style.transform = 'translateY(40px)';
            toast.style.opacity = '0';
            setTimeout(() => {
                if (toast.parentNode) toast.remove();
            }, 500); // tempo da transição
        }
    }, 6000);
}

// Inicia o sistema de social proof
function initSocialProof() {
    // Espera 3 segundos para mostrar o primeiro
    setTimeout(() => {
        createSocialProofToast();
        
        // Depois mostra um novo a cada 15-35 segundos aleatoriamente
        setInterval(() => {
            if (Math.random() > 0.3) { // 70% de chance de mostrar a cada intervalo
                createSocialProofToast();
            }
        }, 20000); 
    }, 3000);
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initSocialProof);
} else {
    initSocialProof();
}
