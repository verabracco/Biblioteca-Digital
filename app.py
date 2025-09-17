from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from db import criar_tabelas, registrar_usuario, buscar_usuario, buscar_livros, buscar_emprestimos_usuario, buscar_historico_usuario, renovar_emprestimo, devolver_emprestimo # Novo: buscar_usuario

app = Flask(__name__)
app.secret_key = 'segredo'

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    dados = request.json
    email = dados.get('email')
    senha = dados.get('senha')
    tipo = dados.get('tipo')

    print(f"Login tentativa: tipo={tipo}, email={email}")

    usuario = buscar_usuario(tipo, email, senha)

    if usuario:
        # usuario = (id, tipo, email, senha) baseado no SELECT * do banco
        session['usuario'] = {
            "id": usuario[0],
            "tipo": usuario[1],
            "email": usuario[2]
        }

        if usuario[1] == 'Aluno':
            return jsonify({"sucesso": True, "redirect": "/aluno"})
        elif usuario[1] == 'Funcionario':
            return jsonify({"sucesso": True, "redirect": "/funcionario"})
    else:
        return jsonify({
            'sucesso': False,
            'mensagem': 'Email, senha ou perfil incorretos.'
        }), 401 

@app.route('/aluno')
def pagina_aluno():
    if 'usuario' not in session or session['usuario']['tipo'] != 'Aluno':
        return redirect(url_for('home'))  # se não estiver logado

    usuario = session['usuario']
    id_usuario = usuario['id']
    print('usuario: ', usuario)

     # Buscar os dados do banco
    livros = buscar_livros()  # retorna lista de todos os livros
    print('livros: ', livros)

    emprestimos = buscar_emprestimos_usuario(id_usuario)  # empréstimos ativos do usuário
    historico = buscar_historico_usuario(id_usuario)  # histórico de empréstimos finalizados
    return render_template('aluno.html', 
                           usuario=usuario,
                           livros=livros, 
                           emprestimos=emprestimos, 
                           historico=historico)


@app.route('/funcionario')
def pagina_funcionario():
    if 'usuario' not in session or session['usuario']['tipo'] != 'Funcionario':
        return redirect(url_for('home'))

    from db import buscar_livros
    livros = buscar_livros()
    return render_template('funcionario.html', livros=livros)


@app.route('/registro', methods=['GET'])
def registro():
    return render_template('registro.html')

@app.route('/registro', methods=['POST'])
def processar_registro():
    tipo = request.form['tipo']
    email = request.form['email']
    senha = request.form['senha']
    
    sucesso, erro = registrar_usuario(tipo, email, senha)
    if sucesso:
        return redirect(url_for('home'))
    else:
        return erro, 400

@app.route('/atualizar_emprestimo', methods=['POST'])
def atualizar_emprestimo():
    dados = request.json
    id_emprestimo = dados.get('id_emprestimo')
    acao = dados.get('acao')

    if acao == 'renovar':
        sucesso, resultado = renovar_emprestimo(id_emprestimo)
        if sucesso:
            return jsonify({'sucesso': True, **resultado})
        else:
            return jsonify({'sucesso': False, 'mensagem': resultado})

    elif acao == 'devolver':
        sucesso, resultado = devolver_emprestimo(id_emprestimo)
        if sucesso:
            return jsonify({'sucesso': True, **resultado})
        else:
            return jsonify({'sucesso': False, 'mensagem': resultado})

    return jsonify({'sucesso': False, 'mensagem': 'Ação inválida'})

@app.route('/solicitar_emprestimo', methods=['POST'])
def solicitar_emprestimo():
    if 'usuario' not in session:
        return jsonify({'sucesso': False, 'mensagem': 'Usuário não autenticado'})

    dados = request.json
    id_livro = dados.get('id_livro')
    id_usuario = session['usuario']['id']

    from db import registrar_emprestimo
    sucesso, dados_retorno = registrar_emprestimo(id_usuario, id_livro)
    
    if sucesso:
        return jsonify({
            'sucesso': True,
            'id_emprestimo': dados_retorno['id_emprestimo'],
            'data_devolucao_formatada': dados_retorno['data_formatada']
        })
    else:
        return jsonify({'sucesso': False, 'mensagem': dados_retorno})

@app.route('/remover_livro/<int:id_livro>', methods=['DELETE'])
def remover_livro(id_livro):
    from db import excluir_livro
    sucesso, msg = excluir_livro(id_livro)
    return jsonify({"sucesso": sucesso, "mensagem": msg})

@app.route('/adicionar_livro', methods=['POST'])
def adicionar_livro():
    if 'usuario' not in session or session['usuario']['tipo'] != 'Funcionario':
        return jsonify({'sucesso': False, 'mensagem': 'Acesso não autorizado'})

    dados = request.get_json()
    from db import inserir_livro

    sucesso, mensagem = inserir_livro(
        titulo=dados.get('titulo'),
        autor=dados.get('autor'),
        ano=dados.get('ano'),
        genero=dados.get('genero'),
        descricao=dados.get('descricao'),
        imagem=dados.get('imagem')
    )

    return jsonify({'sucesso': sucesso, 'mensagem': mensagem})

@app.route('/livro/<int:id_livro>')
def obter_livro(id_livro):
    from db import buscar_livro_por_id
    livro = buscar_livro_por_id(id_livro)
    if livro:
        return jsonify({'sucesso': True, 'livro': livro})
    return jsonify({'sucesso': False, 'mensagem': 'Livro não encontrado'}), 404

@app.route('/editar_livro/<int:id_livro>', methods=['POST'])
def editar_livro(id_livro):
    dados = request.json
    titulo = dados.get('titulo')
    autor = dados.get('autor')
    ano = dados.get('ano')
    genero = dados.get('genero')
    imagem = dados.get('imagem')
    descricao = dados.get('descricao')

    from db import atualizar_livro
    sucesso, erro = atualizar_livro(id_livro, titulo, autor, ano, genero, imagem, descricao)

    if sucesso:
        return jsonify({'sucesso': True})
    else:
        return jsonify({'sucesso': False, 'mensagem': erro}), 400

@app.route('/informacoes_emprestimo/<int:id_livro>')
def informacoes_emprestimo(id_livro):
    """Rota para obter informações do empréstimo de um livro"""
    
    
    from db import obter_informacoes_emprestimo
    emprestimo_info = obter_informacoes_emprestimo(id_livro)
    
    if emprestimo_info:
        email, data_emprestimo, data_devolucao = emprestimo_info
        return jsonify({
            'email': email,
            'data_emprestimo': data_emprestimo,
            'data_devolucao': data_devolucao
        })
    else:
        return jsonify({'error': 'Informações não encontradas'}), 404
    
if __name__ == '__main__':
    criar_tabelas()  # Cria a tabela se não existir
    app.run(debug=True)
