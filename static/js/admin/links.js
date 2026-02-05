/* =========================
   LINKS - Gerenciamento de Links
========================= */

function openEditLink(id, title, desc, img, down, vid, game) {
    setVal('link_edit_id', id);
    setVal('link_title', title);
    setVal('link_desc', desc);
    setVal('link_down', down);
    setVal('link_vid', vid);
    setVal('link_game', game);
    setVal('link_edit_image_url', '');

    const preview = document.getElementById('link_edit_preview');
    if (preview) preview.src = img || '';

    document.getElementById('editLinkModal')?.classList.add('modal-active');
}

async function deleteLink(id) {
    if (!confirm('Confirmar exclusão?')) return;
    await fetch(`/admin/links/delete/${id}`, { method: 'POST' });
    location.reload();
}
