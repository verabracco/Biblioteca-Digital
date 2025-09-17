    function toggleProfile() {
      const section = document.getElementById("profileSection");
      const icon = document.getElementById("toggleIcon");
      const isVisible = section.style.display === "grid";
      section.style.display = isVisible ? "none" : "grid";
      icon.classList.toggle("open", !isVisible);
    }

    window.onload = () => {
      document.getElementById("profileSection").style.display = "none";
      document.getElementById("toggleIcon").classList.remove("open");
    };

async function renovar(id_emprestimo, btn) {
  try {
    const response = await fetch('/atualizar_emprestimo', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ id_emprestimo, acao: 'renovar' })
    });

    const data = await response.json();

    if (!data.sucesso) {
      alert('Erro ao renovar: ' + data.mensagem);
      return;
    }

    // Atualiza a data na interface
    const span = btn.closest('li').querySelector('.data');
    span.textContent = formatarDataParaBR(data.nova_data_devolucao);

    alert("Livro renovado até " + span.textContent);

    // Desabilita botão se atingiu limite
    if (data.renovacoes_atingidas) {
      btn.disabled = true;
    }
  } catch (error) {
    alert('Erro na requisição: ' + error.message);
  }
}

function devolver(id_emprestimo, btn) {
  if (!confirm("Tem certeza que deseja devolver este livro?")) return;

  fetch('/atualizar_emprestimo', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ id_emprestimo: id_emprestimo, acao: 'devolver' })
  })
  .then(res => res.json())
  .then(data => {
    if (data.sucesso) {
      const li = btn.closest('li');
      const titulo = li.textContent.split(' - ')[0].trim();
      li.remove();  // remove da seção "Livros em Empréstimo"

      // adiciona à cronologia
      const cronologia = document.getElementById("cronologia");
      const novoItem = document.createElement("li");
      novoItem.textContent = `${titulo} - ${data.data_devolucao}`;
      cronologia.appendChild(novoItem);

      alert("Livro devolvido com sucesso.");
    } else {
      alert("Erro ao devolver: " + data.mensagem);
    }
  })
  .catch(err => {
    console.error("Erro na requisição:", err);
    alert("Erro inesperado.");
  });
}


// Função auxiliar para formatar 'YYYY-MM-DD' para 'DD/MM/YYYY'
function formatarDataParaBR(dataISO) {
  const partes = dataISO.split('-'); // ['2025', '08', '27']
  return `${partes[2]}/${partes[1]}/${partes[0]}`;
}

  document.getElementById("searchInput").addEventListener("input", function () {
    const termo = this.value.toLowerCase();
    const livros = document.querySelectorAll(".book-box");

    livros.forEach((livro) => {
      const textoLivro = livro.textContent.toLowerCase();
      if (textoLivro.includes(termo)) {
        livro.style.display = "flex";
      } else {
        livro.style.display = "none";
      }
    });
  });  

function solicitarEmprestimo(idLivro, tituloLivro) {
  fetch('/solicitar_emprestimo', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ id_livro: idLivro })
  })
  .then(res => {
    if (!res.ok) {
      // Se o status HTTP for erro (ex: 400, 500), dispara erro manual
      throw new Error(`Erro HTTP: ${res.status}`);
    }
    return res.json();
  })
  .then(res => {
    if (res.sucesso) {
      alert('Empréstimo realizado com sucesso!');

      // Atualiza o botão e status do livro
      const bookBox = document.querySelector(`button[onclick="solicitarEmprestimo(${idLivro}, '${tituloLivro}')"]`).closest('.book-box');
      const statusElement = bookBox.querySelector('.status');

      if (statusElement) {
        statusElement.classList.remove('available');
        statusElement.classList.add('unavailable');
        statusElement.innerHTML = '<span class="dot"></span> Não disponível';
      }

      const solicitarBtn = bookBox.querySelector('.solicitar-btn');
      if (solicitarBtn) {
        solicitarBtn.remove();
      }

      // Atualiza painel de empréstimos
      const emprestimosUl = document.getElementById('emprestimos');
      const novoItem = document.createElement('li');
      novoItem.innerHTML = `
        ${tituloLivro} - devolver até <span class="data">${res.data_devolucao_formatada}</span>
        <div class="action-buttons">
          <button onclick="renovar(${res.id_emprestimo}, this)">Renovar</button>
          <button onclick="devolver(${res.id_emprestimo}, this)">Devolver</button>
        </div>
      `;
      emprestimosUl.appendChild(novoItem);
    } else {
      alert(res.mensagem || 'Erro ao solicitar empréstimo');
    }
  })
  .catch(err => {
    console.error('Erro na requisição:', err);
    alert('Erro na requisição ao solicitar empréstimo.');
  });
}

document.addEventListener('click', function (event) {
  if (event.target.classList.contains('solicitar-btn')) {
    const btn = event.target;
    const idLivro = btn.dataset.id;
    const tituloLivro = btn.dataset.titulo;

    fetch('/solicitar_emprestimo', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ id_livro: idLivro })
    })
    .then(res => {
      if (!res.ok) throw new Error(`Erro HTTP: ${res.status}`);
      return res.json();
    })
    .then(res => {
      if (res.sucesso) {
        alert('Empréstimo realizado com sucesso!');

        const bookBox = btn.closest('.book-box');
        const statusElement = bookBox.querySelector('.status');
        
        if (statusElement) {
          statusElement.classList.remove('available');
          statusElement.classList.add('unavailable');
          statusElement.innerHTML = '<span class="dot"></span> Não disponível';
        }

        btn.remove();

        const emprestimosUl = document.getElementById('emprestimos');
        const novoItem = document.createElement('li');
        novoItem.innerHTML = `
          ${tituloLivro} - devolver até <span class="data">${res.data_devolucao_formatada}</span>
          <div class="action-buttons">
            <button onclick="renovar(${res.id_emprestimo}, this)">Renovar</button>
            <button onclick="devolver(${res.id_emprestimo}, this)">Devolver</button>
          </div>
        `;
        emprestimosUl.appendChild(novoItem);

        // Remove a mensagem "Sem empréstimos no momento", se existir
        const placeholder = emprestimosUl.querySelector('li');
        if (placeholder && placeholder.textContent.includes('Sem empréstimos')) {
          placeholder.remove();
        }

      } else {
        alert(res.mensagem || 'Erro ao solicitar empréstimo');
      }
    })
    .catch(err => {
      console.error('Erro na requisição:', err);
      alert('Erro na requisição ao solicitar empréstimo.');
    });
  }
});
