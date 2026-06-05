let adminPassword = '';

function showStatus() {
    document.getElementById('form-card').style.display = 'none';
    document.getElementById('admin-card').style.display = 'none';
    document.getElementById('status-card').style.display = 'block';
}

function showForm() {
    document.getElementById('status-card').style.display = 'none';
    document.getElementById('admin-card').style.display = 'none';
    document.getElementById('form-card').style.display = 'block';
}

function showAdmin() {
    document.getElementById('form-card').style.display = 'none';
    document.getElementById('status-card').style.display = 'none';
    document.getElementById('admin-card').style.display = 'block';
}

document.getElementById('admin-link')?.addEventListener('click', (e) => {
    e.preventDefault();
    showAdmin();
});

document.getElementById('verificacao-form')?.addEventListener('submit', async (e) => {
    e.preventDefault();

    const btn = document.getElementById('submit-btn');
    const btnText = btn.querySelector('.btn-text');
    const btnLoading = btn.querySelector('.btn-loading');
    btn.disabled = true;
    btnText.style.display = 'none';
    btnLoading.style.display = 'inline';

    const resultDiv = document.getElementById('result');
    resultDiv.style.display = 'none';

    try {
        const res = await fetch('/api/verificar', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                nome: document.getElementById('nome').value.trim(),
                idade: parseInt(document.getElementById('idade').value),
                telefone: document.getElementById('telefone').value.trim(),
                discord_id: document.getElementById('discord').value.trim(),
            }),
        });

        const data = await res.json();

        resultDiv.className = res.ok ? 'success' : 'error';
        resultDiv.textContent = data.message;
        resultDiv.style.display = 'block';

        if (res.ok) {
            document.getElementById('verificacao-form').reset();
        }
    } catch (err) {
        resultDiv.className = 'error';
        resultDiv.textContent = 'Erro ao conectar com o servidor. Tente novamente.';
        resultDiv.style.display = 'block';
    } finally {
        btn.disabled = false;
        btnText.style.display = 'inline';
        btnLoading.style.display = 'none';
    }
});

async function adminLogin() {
    const pwd = document.getElementById('admin-password').value.trim();
    const errorDiv = document.getElementById('admin-login-error');
    if (!pwd) {
        errorDiv.textContent = 'Digite a senha.';
        errorDiv.style.display = 'block';
        return;
    }
    try {
        const res = await fetch('/api/admin/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ password: pwd }),
        });
        if (!res.ok) {
            errorDiv.textContent = 'Senha incorreta.';
            errorDiv.style.display = 'block';
            return;
        }
        adminPassword = pwd;
        document.getElementById('admin-login').style.display = 'none';
        document.getElementById('admin-panel').style.display = 'block';
        await loadAdminVerificacoes();
    } catch {
        errorDiv.textContent = 'Erro ao conectar.';
        errorDiv.style.display = 'block';
    }
}

function adminLogout() {
    adminPassword = '';
    document.getElementById('admin-panel').style.display = 'none';
    document.getElementById('admin-login').style.display = 'block';
    document.getElementById('admin-password').value = '';
    document.getElementById('admin-login-error').style.display = 'none';
    showForm();
}

async function loadAdminVerificacoes() {
    const list = document.getElementById('admin-list');
    list.innerHTML = '<p style="text-align:center;color:rgba(255,255,255,0.4);padding:20px">Carregando...</p>';
    try {
        const res = await fetch(`/api/admin/verificacoes?password=${encodeURIComponent(adminPassword)}`);
        if (!res.ok) { list.innerHTML = '<p style="text-align:center;color:#fca5a5">Erro ao carregar.</p>'; return; }
        const data = await res.json();
        if (!data.length) {
            list.innerHTML = '<p style="text-align:center;color:rgba(255,255,255,0.3);padding:20px">Nenhuma verificação pendente.</p>';
            return;
        }
        let html = '<div style="display:flex;flex-direction:column;gap:12px">';
        for (const v of data) {
            html += `
                <div style="background:rgba(0,0,0,0.3);border-radius:10px;padding:14px;border:1px solid rgba(255,255,255,0.06)">
                    <div style="display:flex;justify-content:space-between;align-items:start;margin-bottom:8px">
                        <strong style="color:#fff;font-size:15px">${escapeHtml(v.nome)}</strong>
                        <span style="font-size:12px;color:rgba(255,255,255,0.3)">#${v.id}</span>
                    </div>
                    <div style="display:grid;grid-template-columns:1fr 1fr;gap:4px;font-size:13px;color:rgba(255,255,255,0.6);margin-bottom:10px">
                        <span>Idade: ${v.idade}</span>
                        <span>Tel: ${v.telefone}</span>
                        <span>Discord: ${v.discord_id || '-'}</span>
                        <span>Origem: ${v.origem || '-'}</span>
                    </div>
                    <div style="font-size:11px;color:rgba(255,255,255,0.25);margin-bottom:10px">${v.created_at || ''}</div>
                    <div style="display:flex;gap:8px">
                        <button onclick="adminAction(${v.id},'aprovado')" style="flex:1;padding:8px;font-size:13px;background:#22c55e;color:#fff;border:none;border-radius:8px;cursor:pointer">Aprovar</button>
                        <button onclick="adminAction(${v.id},'reprovado')" style="flex:1;padding:8px;font-size:13px;background:#ef4444;color:#fff;border:none;border-radius:8px;cursor:pointer">Reprovar</button>
                    </div>
                </div>`;
        }
        html += '</div>';
        list.innerHTML = html;
    } catch {
        list.innerHTML = '<p style="text-align:center;color:#fca5a5">Erro ao carregar.</p>';
    }
}

async function adminAction(id, status) {
    try {
        const res = await fetch(`/api/admin/verificacoes/${id}/status?password=${encodeURIComponent(adminPassword)}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status }),
        });
        if (res.ok) await loadAdminVerificacoes();
    } catch {}
}

function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

document.getElementById('status-form')?.addEventListener('submit', async (e) => {
    e.preventDefault();

    const btn = document.getElementById('status-btn');
    btn.disabled = true;
    btn.textContent = 'Consultando...';

    const resultDiv = document.getElementById('status-result');
    resultDiv.style.display = 'none';

    try {
        const res = await fetch('/api/status', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ telefone: document.getElementById('status-tel').value.trim() }),
        });

        const data = await res.json();
        resultDiv.className = res.ok ? (
            data.status === 'aprovado' ? 'success' :
            data.status === 'reprovado' ? 'error' : 'info'
        ) : 'error';
        resultDiv.textContent = data.message;
        resultDiv.style.display = 'block';
    } catch (err) {
        resultDiv.className = 'error';
        resultDiv.textContent = 'Erro ao consultar. Tente novamente.';
        resultDiv.style.display = 'block';
    } finally {
        btn.disabled = false;
        btn.textContent = 'Consultar';
    }
});
