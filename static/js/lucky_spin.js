// Lógica do Giro da Sorte (Lucky Spin) - RAIO MODS
document.addEventListener('DOMContentLoaded', () => {
    // Carregar elementos
    const fab = document.getElementById('luckySpinFAB');
    const modal = document.getElementById('luckySpinModal');
    const closeBtn = document.getElementById('closeLuckySpin');
    const mainStep = document.getElementById('lucky-spin-main-step');
    const resultStep = document.getElementById('lucky-spin-result-step');
    const emailInput = document.getElementById('luckySpinEmail');
    const spinForm = document.getElementById('luckySpinForm');
    const spinError = document.getElementById('luckySpinError');
    const resultMsg = document.getElementById('luckySpinResultMsg');
    const centerBtn = document.getElementById('wheelSpinBtnCenter');
    const submitBtn = document.getElementById('btnSpinSubmit');
    
    const canvas = document.getElementById('wheelCanvas');
    if (!canvas) return; // Se não estiver na página, aborta
    const ctx = canvas.getContext('2d');
    const wheelWrap = document.querySelector('.wheel-canvas-wrap');
    
    // Configurações das fatias da roleta
    // Índices: 0=5%, 1=8%, 2=5%, 3=10%, 4=8%, 5=12%, 6=5%, 7=15%
    const segments = [
        { text: "5%", value: 5, color: "#1e1b4b", textColor: "#06b6d4" },  // Azul Escuro / Neon Cyan
        { text: "8%", value: 8, color: "#064e3b", textColor: "#10b981" },  // Verde Escuro / Neon Green
        { text: "5%", value: 5, color: "#1e1b4b", textColor: "#06b6d4" },
        { text: "10%", value: 10, color: "#581c87", textColor: "#c084fc" }, // Roxo / Lilás
        { text: "8%", value: 8, color: "#064e3b", textColor: "#10b981" },
        { text: "12%", value: 12, color: "#7c2d12", textColor: "#fb923c" }, // Laranja Escuro / Laranja Neon
        { text: "5%", value: 5, color: "#1e1b4b", textColor: "#06b6d4" },
        { text: "15%", value: 15, color: "#451a03", textColor: "#facc15" }  // Marrom Dourado / Amarelo Ouro
    ];
    
    let isSpinning = false;
    let currentRotationAngle = 0;
    let idleAnimationId = null;
    const idleSpeed = 0.25; // Velocidade do giro ocioso (graus por frame)
    
    // Redimensiona o canvas para alta resolução (Retina display)
    function initCanvasResolution() {
        const size = 500;
        canvas.width = size;
        canvas.height = size;
    }
    
    // Desenha a roleta no canvas
    function drawWheel() {
        const size = canvas.width;
        const center = size / 2;
        const radius = center - 12;
        
        ctx.clearRect(0, 0, size, size);
        
        const sliceAngle = (2 * Math.PI) / segments.length;
        
        for (let i = 0; i < segments.length; i++) {
            const startAngle = i * sliceAngle;
            const endAngle = startAngle + sliceAngle;
            
            // Fila de pizza
            ctx.beginPath();
            ctx.moveTo(center, center);
            ctx.arc(center, center, radius, startAngle, endAngle);
            ctx.fillStyle = segments[i].color;
            ctx.fill();
            
            // Divisórias das fatias
            ctx.strokeStyle = "rgba(255, 255, 255, 0.08)";
            ctx.lineWidth = 3;
            ctx.stroke();
            
            // Desenhar texto
            ctx.save();
            ctx.translate(center, center);
            ctx.rotate(startAngle + sliceAngle / 2);
            ctx.textAlign = "right";
            ctx.textBaseline = "middle";
            ctx.fillStyle = segments[i].textColor;
            ctx.font = "bold 28px 'Sora', sans-serif";
            
            // Efeito de brilho neon no texto
            ctx.shadowBlur = 8;
            ctx.shadowColor = segments[i].textColor;
            
            ctx.fillText(segments[i].text, radius - 35, 0);
            ctx.restore();
        }
        
        // Bordas e círculos decorativos centrais
        ctx.beginPath();
        ctx.arc(center, center, 40, 0, 2 * Math.PI);
        ctx.fillStyle = "rgba(6, 182, 212, 0.15)";
        ctx.fill();
        ctx.strokeStyle = "rgba(6, 182, 212, 0.3)";
        ctx.lineWidth = 2;
        ctx.stroke();
    }
    
    // Loop de Animação do Giro Lento (Idle)
    function startIdleSpin() {
        if (isSpinning) return;
        
        // Remove a transição CSS enquanto roda via loop para não lagar
        if (wheelWrap) {
            wheelWrap.style.transition = 'none';
        }
        
        function tick() {
            currentRotationAngle = (currentRotationAngle + idleSpeed) % 360;
            if (wheelWrap) {
                wheelWrap.style.transform = `rotate(${currentRotationAngle}deg)`;
            }
            idleAnimationId = requestAnimationFrame(tick);
        }
        
        if (!idleAnimationId) {
            idleAnimationId = requestAnimationFrame(tick);
        }
    }
    
    function stopIdleSpin() {
        if (idleAnimationId) {
            cancelAnimationFrame(idleAnimationId);
            idleAnimationId = null;
        }
    }
    
    initCanvasResolution();
    drawWheel();
    
    // Verifica se já girou nos últimos 30 dias (UX cache local)
    function checkLocalStorageSpin() {
        const lastSpinDateStr = localStorage.getItem('last_lucky_spin_date');
        if (lastSpinDateStr) {
            const lastSpinDate = new Date(lastSpinDateStr);
            const diffTime = Math.abs(new Date() - lastSpinDate);
            const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
            
            if (diffDays <= 30) {
                if (fab) fab.classList.add('hidden');
            }
        }
    }
    
    checkLocalStorageSpin();
    
    // Abrir o Modal
    if (fab) {
        fab.addEventListener('click', () => {
            modal.classList.remove('hidden');
            modal.classList.add('flex');
            
            mainStep.classList.remove('hidden');
            resultStep.classList.add('hidden');
            spinError.classList.add('hidden');
            emailInput.value = '';
            
            // Re-ativa o botão e input caso estivessem desativados
            emailInput.disabled = false;
            submitBtn.disabled = false;
            submitBtn.innerHTML = '🎰 Girar Roleta';
            centerBtn.classList.remove('disabled');
            centerBtn.innerHTML = 'Girar';
            
            // Reseta a rotação e inicia o giro lento
            currentRotationAngle = 0;
            startIdleSpin();
        });
    }
    
    // Fechar o Modal
    function closeModal() {
        if (isSpinning) return; // Bloqueia fechar durante o giro rápido
        stopIdleSpin();
        modal.classList.add('hidden');
        modal.classList.remove('flex');
    }
    
    if (closeBtn) closeBtn.addEventListener('click', closeModal);
    if (modal) {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) closeModal();
        });
    }
    
    // Ao clicar no botão central da roleta, submete o formulário
    if (centerBtn) {
        centerBtn.addEventListener('click', () => {
            if (isSpinning) return;
            
            // Submete o formulário disparando as validações nativas do navegador
            if (typeof spinForm.requestSubmit === 'function') {
                spinForm.requestSubmit();
            } else {
                const triggerBtn = spinForm.querySelector('button[type="submit"]');
                if (triggerBtn) triggerBtn.click();
            }
        });
    }
    
    // Envio do formulário (Girar)
    if (spinForm) {
        spinForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            if (isSpinning) return;
            
            const email = emailInput.value.trim();
            if (!email || !email.includes('@')) {
                showError('Por favor, insira um e-mail válido.');
                return;
            }
            
            spinError.classList.add('hidden');
            emailInput.disabled = true;
            submitBtn.disabled = true;
            submitBtn.innerHTML = '🔄 Processando...';
            centerBtn.classList.add('disabled');
            centerBtn.innerHTML = '⏳';
            
            try {
                const res = await fetch('/api/spin', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email: email })
                });
                
                const data = await res.json();
                
                if (data.error) {
                    showError(data.error);
                    emailInput.disabled = false;
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = '🎰 Girar Roleta';
                    centerBtn.classList.remove('disabled');
                    centerBtn.innerHTML = 'Girar';
                    return;
                }
                
                // 1. Para o loop do giro lento para iniciar o giro rápido
                stopIdleSpin();
                isSpinning = true;
                submitBtn.innerHTML = '🎰 Girando...';
                centerBtn.innerHTML = '🔥';
                
                // 2. Mapeia o desconto para as fatias correspondentes
                const matchedIndices = [];
                segments.forEach((seg, idx) => {
                    if (seg.value === data.discount) {
                        matchedIndices.push(idx);
                    }
                });
                
                const winningSegmentIndex = matchedIndices[Math.floor(Math.random() * matchedIndices.length)];
                
                // 3. Calcula a rotação rápida com base no ângulo atual
                // Garante transição perfeita somando voltas completas e compensando a fatia sorteada
                const rotations = 6;
                const degreesPerSegment = 360 / segments.length;
                
                // Fórmula matemática de precisão:
                // Alinha o centro da fatia sorteada com a seta superior (12 horas, que fica a -90 graus)
                const baseMultiple = currentRotationAngle - (currentRotationAngle % 360);
                const targetRotation = baseMultiple + (rotations * 360) - (winningSegmentIndex * degreesPerSegment + degreesPerSegment / 2) - 90;
                
                // Executa a transição física com easing suave
                setTimeout(() => {
                    if (wheelWrap) {
                        wheelWrap.style.transition = 'transform 5s cubic-bezier(0.1, 0.8, 0.1, 1)';
                        wheelWrap.style.transform = `rotate(${targetRotation}deg)`;
                    }
                }, 50);
                
                // 4. Aguarda o término da animação do giro (5 segundos)
                setTimeout(() => {
                    isSpinning = false;
                    
                    // Salva data no localStorage para sumir com o FAB
                    localStorage.setItem('last_lucky_spin_date', new Date().toISOString());
                    if (fab) fab.classList.add('hidden');
                    
                    // Exibir resultado final
                    mainStep.classList.add('hidden');
                    resultStep.classList.remove('hidden');
                    
                    resultMsg.innerHTML = `
                        <div class="text-3xl font-extrabold text-neon-green mb-2" style="font-family: 'Sora', sans-serif;">🎉 GANHOU ${data.discount}%!</div>
                        <p class="text-gray-300 text-sm mb-4">
                            Seu cupom de desconto exclusivo de <strong>${data.discount}%</strong> foi gerado com sucesso e enviado para:
                        </p>
                        <div class="bg-black/60 border border-white/10 rounded-lg p-2.5 mb-4 text-white font-mono break-all font-semibold">
                            ${email}
                        </div>
                        <p class="text-xs text-yellow-500 font-bold mb-4">
                            ⚠️ Verifique sua caixa de entrada e pasta de Spam. O cupom expira em 24 horas!
                        </p>
                    `;
                }, 5300);
                
            } catch (err) {
                console.error(err);
                showError('Ocorreu um erro ao conectar ao servidor. Tente novamente.');
                emailInput.disabled = false;
                submitBtn.disabled = false;
                submitBtn.innerHTML = '🎰 Girar Roleta';
                centerBtn.classList.remove('disabled');
                centerBtn.innerHTML = 'Girar';
            }
        });
    }
    
    function showError(msg) {
        spinError.innerText = msg;
        spinError.classList.remove('hidden');
    }
});
