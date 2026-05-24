function showStatus() {
    document.getElementById('form-card').style.display = 'none';
    document.getElementById('status-card').style.display = 'block';
}

function showForm() {
    document.getElementById('status-card').style.display = 'none';
    document.getElementById('form-card').style.display = 'block';
}

document.getElementById('verificacao-form').addEventListener('submit', async (e) => {
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

document.getElementById('status-form').addEventListener('submit', async (e) => {
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
