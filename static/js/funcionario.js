function abrirFormularioNovoLivro(editar = false) {
  const modal = document.getElementById('formLivro');
  const tituloModal = modal.querySelector('h2'); // Captura o título do modal

if (editar) {
    tituloModal.innerText = 'Editar Livro'; // Muda o título
  } else {
    tituloModal.innerText = 'Adicionar Novo Livro'; // Muda o título
  }

  modal.style.display = 'block';
}

function fecharModalLivro() {
  const modal = document.getElementById('formLivro');
  modal.style.display = 'none';

  const form = document.getElementById('formNovoLivro');
  form.reset();
  delete form.dataset.editando; // Limpa o modo de edição
}


function editarLivro(idLivro) {
  console.log("Buscando livro ID:", idLivro);

  fetch(`/livro/${idLivro}`)
    .then(res => res.json())
    .then(data => {
      if (data.sucesso) {
        const livro = data.livro;

        const form = document.getElementById('formNovoLivro');
        form.titulo.value = livro.titulo;
        form.autor.value = livro.autor;
        form.ano.value = livro.ano;
        form.descricao.value = livro.descricao;
        form.genero.value = livro.genero;
        form.imagem.value = livro.imagem;

        // Guarda o ID do livro para salvar depois
        form.dataset.editando = livro.id;

        abrirFormularioNovoLivro(true);
      } else {
        alert("Livro não encontrado.");
      }
    })
    .catch(err => {
      console.error("Erro ao buscar livro:", err);
      alert("Erro ao buscar livro.");
    });
}

function removerLivro(idLivro) {
  if (confirm("Deseja realmente remover este livro?")) {
    fetch(`/remover_livro/${idLivro}`, {
      method: 'DELETE'
    })
    .then(res => res.json())
    .then(data => {
      if (data.sucesso) {
        alert("Livro removido com sucesso!");
        location.reload();
      } else {
        alert("Erro: " + data.mensagem);
      }
    })
    .catch(err => {
      console.error(err);
      alert("Erro ao remover livro.");
    });
  }
}

document.getElementById('formNovoLivro').addEventListener('submit', function (e) {
  e.preventDefault();

  const form = this;
  const dadosLivro = {
    titulo: form.titulo.value,
    autor: form.autor.value,
    ano: form.ano.value,
    descricao: form.descricao.value,
    genero: form.genero.value,
    imagem: form.imagem.value
  };

  const idEditando = form.dataset.editando;

  const url = idEditando ? `/editar_livro/${idEditando}` : '/adicionar_livro';

  fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(dadosLivro)
  })
    .then(res => res.json())
    .then(data => {
      if (data.sucesso) {
        fecharModalLivro();
        window.location.reload(); // atualiza a lista
      } else {
        alert(data.mensagem || 'Erro ao salvar livro.');
      }
    });
});

function verInfoEmprestimo(idLivro) {
  fetch(`/informacoes_emprestimo/${idLivro}`)
    .then(response => response.json())
    .then(data => {
      if (data.error) {
        alert('Erro ao carregar informações');
      } else {
        document.getElementById('nomeAluno').textContent = data.email;
        document.getElementById('dataRetirada').textContent = data.data_emprestimo;
        document.getElementById('dataDevolucao').textContent = data.data_devolucao;
        document.getElementById('modalEmprestimo').style.display = 'block';
      }
    });
}

function fecharModalEmprestimo() {
  document.getElementById('modalEmprestimo').style.display = 'none';
}

