document.getElementById('sortearBtn').addEventListener('click', async () => {
    const username = document.getElementById('usernameInput').value;
    const resultadoDiv = document.getElementById('resultado');
    
    if (!username) {
        resultadoDiv.innerText = 'Por favor, insira um nome de usuário.';
        return;
    }
    
    resultadoDiv.innerText = 'Sorteando...';
    
    try {
        const response = await fetch(`http://127.0.0.1:8000/sortear/${username}`);
        const data = await response.json();
        
        if (response.ok) {
            if (data.filme_link) {
                resultadoDiv.innerHTML = `
                    Filme Sorteado: 
                    <a href="${data.filme_link}" target="_blank" style="color: #00542eff; text-decoration: none;">
                        ${data.filme_sorteado}
                    </a>
                `;
            } else {
                resultadoDiv.innerText = `Filme Sorteado: ${data.filme_sorteado}`;
            }
        } else {
            resultadoDiv.innerText = `Erro: ${data.erro}`;
        }
    } catch (error) {
        resultadoDiv.innerText = 'Erro ao conectar com o servidor.';
    }
});