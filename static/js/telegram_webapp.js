(function() {
    // Intercepta a chamada global de fetch para injetar initData do Telegram WebApp
    const originalFetch = window.fetch;
    window.fetch = async function(...args) {
        const [url, config] = args;
        
        // Verifica se a chamada é o checkout da API
        if (typeof url === 'string' && url.includes('/api/checkout') && config && config.method === 'POST') {
            try {
                const body = JSON.parse(config.body);
                
                // Se estiver rodando dentro do Telegram WebApp, injeta initData
                if (window.Telegram && window.Telegram.WebApp && window.Telegram.WebApp.initData) {
                    body.init_data = window.Telegram.WebApp.initData;
                    config.body = JSON.stringify(body);
                    console.log("Telegram initData injetado com sucesso no checkout.");
                }
            } catch (e) {
                console.error("Erro ao interceptar checkout para Telegram:", e);
            }
        }
        return originalFetch.apply(this, args);
    };
})();
