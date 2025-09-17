  let perfilAtual = '';

  function showLogin(tipo) {
    perfilAtual = tipo;
    const welcome = document.getElementById('welcome-container');
    const login = document.getElementById('login-container');
    const title = document.getElementById('login-title');

    welcome.classList.remove('show');
    welcome.classList.add('hide');

    setTimeout(() => {
      welcome.style.display = 'none';
      login.style.display = 'block';
      setTimeout(() => login.classList.add('show'), 10);
      title.textContent = 'Login ' + tipo;
    }, 500);
  }

    function closeLogin() {
    const welcome = document.getElementById('welcome-container');
    const login = document.getElementById('login-container');

    // Esconde o box de login com animação
    login.classList.remove('show');
    login.classList.add('hide');

    // Após a animação, esconde completamente o login e mostra o welcome
    setTimeout(() => {
        login.style.display = 'none';
        login.classList.remove('hide');
        welcome.style.display = 'block';
        
        // Força a classe de entrada novamente
        setTimeout(() => {
        welcome.classList.remove('hide');
        welcome.classList.add('show');
        }, 10);
    }, 500);
    }


const errorDiv = document.getElementById('login-error');

document.querySelector('#login-form').addEventListener('submit', function (e) {
  e.preventDefault();
  
  // Limpa mensagens anteriores
  errorDiv.style.display = 'none';
  errorDiv.textContent = '';

  const email = this.querySelector('input[type="email"]').value.trim();
  const senha = this.querySelector('input[type="password"]').value;

  fetch('/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, senha, tipo: perfilAtual })
  })
  .then(res => {
    if (!res.ok) {
      return res.json().then(data => {
        throw new Error(data.mensagem || 'Erro desconhecido');
      });
    }
    return res.json();
  })
  .then(data => {
    window.location.href = data.redirect;
  })
  .catch(err => {
    // Exibe a mensagem de erro na div
    errorDiv.textContent = err.message;
    errorDiv.style.display = 'block';
  });
});
