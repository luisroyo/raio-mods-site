/* ==========================================================
   RAIO MODS — Premium Interactive Visual Effects
   ========================================================== */

document.addEventListener('DOMContentLoaded', () => {
    // 1. TYPEWRITER EFFECT (Hero Title)
    const heroTitle = document.querySelector('.hero-title');
    if (heroTitle) {
        const text = heroTitle.textContent.trim();
        heroTitle.innerHTML = ''; // Clear original text
        
        let i = 0;
        const speed = 120; // time in ms per character
        
        const textSpan = document.createElement('span');
        const cursorSpan = document.createElement('span');
        cursorSpan.className = 'typewriter-cursor';
        cursorSpan.textContent = '|';
        
        heroTitle.appendChild(textSpan);
        heroTitle.appendChild(cursorSpan);
        
        function typeWriter() {
            if (i < text.length) {
                textSpan.textContent += text.charAt(i);
                i++;
                setTimeout(typeWriter, speed);
            } else {
                cursorSpan.classList.add('blink');
                // Auto-fade out cursor after 3 seconds
                setTimeout(() => {
                    cursorSpan.style.opacity = '0';
                    cursorSpan.style.transition = 'opacity 1s ease';
                }, 3000);
            }
        }
        
        // Start effect after a brief delay
        setTimeout(typeWriter, 300);
    }
    
    // 2. 3D CARD TILT EFFECT (Product & Catalog Cards)
    const cards = document.querySelectorAll('.card-base');
    
    cards.forEach(card => {
        // Ensure card styles support 3D transforms properly
        card.style.transformStyle = 'preserve-3d';
        card.style.willChange = 'transform';
        
        // Create dynamic glare element
        const glare = document.createElement('div');
        glare.className = 'card-glare';
        glare.style.position = 'absolute';
        glare.style.top = '0';
        glare.style.left = '0';
        glare.style.width = '100%';
        glare.style.height = '100%';
        glare.style.borderRadius = 'inherit';
        glare.style.pointerEvents = 'none';
        glare.style.zIndex = '5';
        glare.style.opacity = '0';
        glare.style.transition = 'opacity 0.4s ease';
        glare.style.background = 'radial-gradient(circle at 50% 50%, rgba(255, 255, 255, 0.15) 0%, transparent 60%)';
        card.appendChild(glare);
        
        card.addEventListener('mousemove', e => {
            const rect = card.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            
            const w = rect.width;
            const h = rect.height;
            
            const normalizedX = x / w;
            const normalizedY = y / h;
            
            // Limit rotation to 10 degrees for elegant sub-rotation
            const maxRotation = 10;
            const rotateX = ((0.5 - normalizedY) * maxRotation).toFixed(2);
            const rotateY = ((normalizedX - 0.5) * maxRotation).toFixed(2);
            
            card.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) scale3d(1.02, 1.02, 1.02)`;
            
            // Calculate dynamic glare gradient position
            const glarePercentX = (normalizedX * 100).toFixed(1);
            const glarePercentY = (normalizedY * 100).toFixed(1);
            glare.style.opacity = '1';
            glare.style.background = `radial-gradient(circle at ${glarePercentX}% ${glarePercentY}%, rgba(255, 255, 255, 0.15) 0%, rgba(6, 182, 212, 0.05) 50%, transparent 80%)`;
        });
        
        card.addEventListener('mouseenter', () => {
            card.style.transition = 'none';
        });
        
        card.addEventListener('mouseleave', () => {
            card.style.transition = 'transform 0.5s cubic-bezier(0.25, 1, 0.5, 1)';
            card.style.transform = 'perspective(1000px) rotateX(0deg) rotateY(0deg) scale3d(1, 1, 1)';
            glare.style.opacity = '0';
        });
    });
});
