let allFeedbacks = [];
let currentFilter = 'all';

document.addEventListener('DOMContentLoaded', () => {
    loadFeedbacks();
});

async function loadFeedbacks() {
    const container = document.getElementById('feedbacksContainer');
    try {
        const res = await fetch('/admin/feedbacks/list');
        if (!res.ok) throw new Error('Não foi possível carregar os feedbacks');
        allFeedbacks = await res.json();
        
        updateTabCounts();
        renderFeedbacks();
    } catch (err) {
        console.error(err);
        if (container) {
            container.innerHTML = `
                <div class="col-span-full text-center py-12 text-red-500 font-semibold bg-red-950/20 border border-red-900/40 rounded-xl">
                    Erro ao carregar feedbacks: ${err.message}
                </div>
            `;
        }
    }
}

function updateTabCounts() {
    const counts = {
        all: allFeedbacks.length,
        pending: allFeedbacks.filter(f => f.status === 'pending').length,
        approved: allFeedbacks.filter(f => f.status === 'approved').length,
        rejected: allFeedbacks.filter(f => f.status === 'rejected').length
    };
    
    document.getElementById('count-all').innerText = counts.all;
    document.getElementById('count-pending').innerText = counts.pending;
    document.getElementById('count-approved').innerText = counts.approved;
    document.getElementById('count-rejected').innerText = counts.rejected;
}

function filterFeedbacks(status) {
    currentFilter = status;
    
    // Atualiza classes ativas nos botões das abas
    const tabs = ['all', 'pending', 'approved', 'rejected'];
    tabs.forEach(t => {
        const btn = document.getElementById(`tab-${t}`);
        if (!btn) return;
        
        if (t === status) {
            btn.classList.add('ring-2', 'ring-rose-500', 'bg-gray-700');
        } else {
            btn.classList.remove('ring-2', 'ring-rose-500', 'bg-gray-700');
        }
    });
    
    renderFeedbacks();
}

function renderFeedbacks() {
    const container = document.getElementById('feedbacksContainer');
    if (!container) return;
    
    const filtered = allFeedbacks.filter(f => {
        if (currentFilter === 'all') return true;
        return f.status === currentFilter;
    });
    
    if (filtered.length === 0) {
        container.innerHTML = `
            <div class="col-span-full text-center py-12 text-gray-500 bg-gray-900/30 border border-gray-800 rounded-xl">
                Nenhum feedback encontrado nesta categoria.
            </div>
        `;
        return;
    }
    
    container.innerHTML = filtered.map(f => {
        // Estrelas
        let stars = '';
        for (let i = 1; i <= 5; i++) {
            stars += i <= f.rating ? '★' : '☆';
        }
        
        // Cor do status
        let statusBadge = '';
        if (f.status === 'pending') {
            statusBadge = '<span class="bg-yellow-500/20 text-yellow-400 text-[10px] font-bold px-2 py-0.5 rounded border border-yellow-500/30">⏳ Pendente</span>';
        } else if (f.status === 'approved') {
            statusBadge = '<span class="bg-green-500/20 text-green-400 text-[10px] font-bold px-2 py-0.5 rounded border border-green-500/30">✅ Aprovado</span>';
        } else {
            statusBadge = '<span class="bg-red-500/20 text-red-400 text-[10px] font-bold px-2 py-0.5 rounded border border-red-500/30">❌ Rejeitado</span>';
        }
        
        // Produto opcional
        const productBadge = f.product_name 
            ? `<span class="bg-cyan-500/10 text-cyan-400 text-[10px] font-bold px-2 py-0.5 rounded border border-cyan-500/20 ml-2">📦 ${f.product_name}</span>`
            : '';
            
        // Botões de ação
        let actionButtons = '';
        if (f.status === 'pending') {
            actionButtons += `
                <button onclick="approveFeedback(${f.id})" class="flex-1 py-1.5 bg-green-600 hover:bg-green-500 text-black text-xs font-bold uppercase rounded transition-colors">Aprovar</button>
                <button onclick="rejectFeedback(${f.id})" class="flex-1 py-1.5 bg-yellow-600 hover:bg-yellow-500 text-black text-xs font-bold uppercase rounded transition-colors">Rejeitar</button>
            `;
        } else if (f.status === 'approved') {
            actionButtons += `
                <button onclick="rejectFeedback(${f.id})" class="flex-1 py-1.5 bg-yellow-600/20 hover:bg-yellow-600/40 text-yellow-500 text-xs font-bold uppercase rounded transition-colors border border-yellow-500/30">Ocultar</button>
            `;
        } else if (f.status === 'rejected') {
            actionButtons += `
                <button onclick="approveFeedback(${f.id})" class="flex-1 py-1.5 bg-green-600/20 hover:bg-green-600/40 text-green-400 text-xs font-bold uppercase rounded transition-colors border border-green-500/30">Aprovar</button>
            `;
        }
        
        // Data formatada
        const dateStr = f.created_at ? new Date(f.created_at.replace(' ', 'T') + 'Z').toLocaleDateString('pt-BR') : '---';
        
        return `
            <div class="bg-gray-900 border-2 border-gray-800 rounded-xl p-5 hover:border-rose-500/30 transition duration-300 flex flex-col justify-between">
                <div>
                    <div class="flex justify-between items-start mb-3">
                        <div class="star-rating text-lg font-bold">${stars}</div>
                        <div class="flex items-center gap-1">
                            ${statusBadge}
                        </div>
                    </div>
                    
                    <p class="text-gray-200 text-sm italic mb-4">"${f.comment}"</p>
                </div>
                
                <div class="border-t border-gray-800 pt-4 mt-auto">
                    <div class="flex justify-between items-end mb-4">
                        <div>
                            <h4 class="text-white font-bold text-sm">${f.client_name}</h4>
                            <p class="text-gray-500 text-xs">${f.client_email || ''}</p>
                        </div>
                        <span class="text-gray-600 text-xs">${dateStr}</span>
                    </div>
                    
                    <div class="mb-4">
                        ${productBadge}
                    </div>
                    
                    <div class="flex gap-2 border-t border-gray-800/50 pt-3">
                        ${actionButtons}
                        <button onclick="deleteFeedback(${f.id})" class="px-3 py-1.5 bg-red-600/10 hover:bg-red-600 text-red-500 hover:text-white text-xs font-bold uppercase rounded border border-red-500/20 hover:border-red-500 transition-colors">Excluir</button>
                    </div>
                </div>
            </div>
        `;
    }).join('');
}

async function approveFeedback(id) {
    try {
        const res = await fetch(`/admin/feedbacks/approve/${id}`, { method: 'POST' });
        const data = await res.json();
        if (data.success) {
            loadFeedbacks();
        } else {
            alert('Erro ao aprovar feedback: ' + data.error);
        }
    } catch (err) {
        alert('Erro ao conectar ao servidor: ' + err.message);
    }
}

async function rejectFeedback(id) {
    try {
        const res = await fetch(`/admin/feedbacks/reject/${id}`, { method: 'POST' });
        const data = await res.json();
        if (data.success) {
            loadFeedbacks();
        } else {
            alert('Erro ao rejeitar feedback: ' + data.error);
        }
    } catch (err) {
        alert('Erro ao conectar ao servidor: ' + err.message);
    }
}

async function deleteFeedback(id) {
    if (!confirm('Tem certeza de que deseja excluir permanentemente este feedback?')) return;
    try {
        const res = await fetch(`/admin/feedbacks/delete/${id}`, { method: 'POST' });
        const data = await res.json();
        if (data.success) {
            loadFeedbacks();
        } else {
            alert('Erro ao excluir feedback: ' + data.error);
        }
    } catch (err) {
        alert('Erro ao conectar ao servidor: ' + err.message);
    }
}
