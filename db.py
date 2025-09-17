import sqlite3
from datetime import datetime, timedelta

def criar_tabelas():
    with sqlite3.connect('biblioteca.db') as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS livros (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                titulo TEXT NOT NULL,
                autor TEXT NOT NULL,
                ano TEXT,
                descricao TEXT,
                genero TEXT,
                imagem TEXT,
                status TEXT NOT NULL DEFAULT 'disponivel'  -- 'disponivel' ou 'emprestado'
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS emprestimos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                id_usuario INTEGER NOT NULL,
                id_livro INTEGER NOT NULL,
                data_emprestimo TEXT NOT NULL,
                data_devolucao_prevista TEXT NOT NULL,
                renovacoes INTEGER DEFAULT 0,
                status TEXT NOT NULL DEFAULT 'ativo',  -- 'ativo' ou 'finalizado'
                FOREIGN KEY (id_usuario) REFERENCES usuarios(id),
                FOREIGN KEY (id_livro) REFERENCES livros(id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS historico (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                id_usuario INTEGER NOT NULL,
                id_livro INTEGER NOT NULL,
                data_emprestimo TEXT NOT NULL,
                data_devolucao TEXT NOT NULL,
                FOREIGN KEY (id_usuario) REFERENCES usuarios(id),
                FOREIGN KEY (id_livro) REFERENCES livros(id)
            )
        ''')

        conn.commit()

def registrar_usuario(tipo, email, senha):
    try:
        with sqlite3.connect('biblioteca.db') as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO usuarios (tipo, email, senha) VALUES (?, ?, ?)', (tipo, email, senha))
            conn.commit()
            return True, None
    except sqlite3.IntegrityError:
        return False, 'Email já cadastrado.'

def buscar_usuario(tipo, email, senha):
    with sqlite3.connect('biblioteca.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM usuarios WHERE tipo = ? AND email = ? AND senha = ?', (tipo, email, senha))
        return cursor.fetchone()

def buscar_livros():
    with sqlite3.connect('biblioteca.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT id, titulo, autor, ano, descricao, genero, imagem, status FROM livros')
        resultado = cursor.fetchall()
        print("resultado banco: ", resultado)
        return resultado

def buscar_emprestimos_usuario(id_usuario):
    with sqlite3.connect('biblioteca.db') as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT livros.id, livros.titulo, emprestimos.data_devolucao_prevista, emprestimos.renovacoes
            FROM emprestimos
            JOIN livros ON emprestimos.id_livro = livros.id
            WHERE emprestimos.id_usuario = ? AND emprestimos.status = 'ativo'
        ''', (id_usuario,))
        return cursor.fetchall()

def buscar_historico_usuario(id_usuario):
    with sqlite3.connect('biblioteca.db') as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT livros.titulo, historico.data_emprestimo, historico.data_devolucao
            FROM historico
            JOIN livros ON historico.id_livro = livros.id
            WHERE historico.id_usuario = ?
        ''', (id_usuario,))
        return cursor.fetchall()

def renovar_emprestimo(id_emprestimo):
    with sqlite3.connect('biblioteca.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT renovacoes, status, data_devolucao_prevista FROM emprestimos WHERE id = ?', (id_emprestimo,))
        res = cursor.fetchone()
        if not res:
            return False, 'Empréstimo não encontrado'
        renovacoes, status, data_devolucao_prevista = res
        if status != 'ativo':
            return False, 'Empréstimo já finalizado'
        if renovacoes >= 5:
            return False, 'Limite de renovações atingido'
        
        nova_data = datetime.strptime(data_devolucao_prevista, '%Y-%m-%d') + timedelta(days=7)
        nova_data_str = nova_data.strftime('%Y-%m-%d')
        
        cursor.execute('UPDATE emprestimos SET renovacoes = renovacoes + 1, data_devolucao_prevista = ? WHERE id = ?', (nova_data_str, id_emprestimo))
        conn.commit()
        
        return True, {'nova_data_devolucao': nova_data_str, 'renovacoes_atingidas': renovacoes + 1 >= 2}

def devolver_emprestimo(id_emprestimo):
    with sqlite3.connect('biblioteca.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT id_usuario, id_livro, status, data_emprestimo FROM emprestimos WHERE id = ?', (id_emprestimo,))
        res = cursor.fetchone()
        if not res:
            return False, 'Empréstimo não encontrado'
        id_usuario, id_livro, status, data_emprestimo = res
        if status != 'ativo':
            return False, 'Empréstimo já finalizado'
        
        data_devolucao = datetime.now().strftime('%Y-%m-%d')
        
        cursor.execute('UPDATE emprestimos SET status = "finalizado" WHERE id = ?', (id_emprestimo,))
        cursor.execute('INSERT INTO historico (id_usuario, id_livro, data_emprestimo, data_devolucao) VALUES (?, ?, ?, ?)',
                       (id_usuario, id_livro, data_emprestimo, data_devolucao))
        
        # Atualiza o status do livro para 'disponivel'
        cursor.execute('UPDATE livros SET status = "disponivel" WHERE id = ?', (id_livro,))
        conn.commit()
        
        return True, {'data_devolucao': data_devolucao}
    
def registrar_emprestimo(id_usuario, id_livro):
    from datetime import datetime, timedelta
    data_emprestimo = datetime.now()
    data_devolucao = data_emprestimo + timedelta(days=7)
    
    data_str = data_emprestimo.strftime('%Y-%m-%d')
    data_devolucao_str = data_devolucao.strftime('%Y-%m-%d')
    data_formatada = data_devolucao.strftime('%d/%m/%Y')

    try:
        with sqlite3.connect('biblioteca.db') as conn:
            cursor = conn.cursor()
            
            # Verifica se o livro já está emprestado
            cursor.execute('SELECT status FROM livros WHERE id = ?', (id_livro,))
            livro = cursor.fetchone()
            if not livro or livro[0] != 'disponivel':
                return False, 'Livro não está disponível para empréstimo.'
            
            # Insere empréstimo
            cursor.execute('''
                INSERT INTO emprestimos (id_usuario, id_livro, data_emprestimo, data_devolucao_prevista)
                VALUES (?, ?, ?, ?)
            ''', (id_usuario, id_livro, data_str, data_devolucao_str))
            
            # Atualiza status do livro
            cursor.execute('UPDATE livros SET status = "emprestado" WHERE id = ?', (id_livro,))
            
            conn.commit()
            
            id_emprestimo = cursor.lastrowid
            
            return True, {'id_emprestimo': id_emprestimo, 'data_formatada': data_formatada}
    except Exception as e:
        return False, str(e)

def excluir_livro(id_livro):
    try:
        with sqlite3.connect('biblioteca.db') as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM livros WHERE id = ?', (id_livro,))
            conn.commit()
            return True, "Livro excluído"
    except Exception as e:
        return False, str(e)

def inserir_livro(titulo, autor, ano, genero, descricao, imagem):
    try:
        with sqlite3.connect('biblioteca.db') as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO livros (titulo, autor, ano, genero, descricao, imagem, status)
                VALUES (?, ?, ?, ?, ?, ?, 'disponivel')
            ''', (titulo, autor, ano, genero, descricao, imagem))
            conn.commit()
            return True, "Livro inserido com sucesso"
    except Exception as e:
        return False, str(e)

def buscar_livro_por_id(id_livro):
    with sqlite3.connect('biblioteca.db') as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, titulo, autor, ano, descricao, genero, imagem, status
            FROM livros WHERE id = ?
        ''', (id_livro,))
        row = cursor.fetchone()
        if row:
            keys = ['id', 'titulo', 'autor', 'ano', 'descricao', 'genero', 'imagem', 'status']
            return dict(zip(keys, row))
        return None

def atualizar_livro(id_livro, titulo, autor, ano, genero, imagem, descricao):
    try:
        with sqlite3.connect('biblioteca.db') as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE livros
                SET titulo = ?, autor = ?, ano = ?, genero = ?, imagem = ?, descricao = ?
                WHERE id = ?
            ''', (titulo, autor, ano, genero, imagem, descricao, id_livro))
            conn.commit()
            return True, None
    except Exception as e:
        return False, str(e)

def obter_informacoes_emprestimo(id_livro):
    """Consulta as informações de empréstimo de um livro específico no banco de dados"""
    
    # Conectando ao banco de dados
    with sqlite3.connect('biblioteca.db') as conn:
        cursor = conn.cursor()
        
        # Executando a consulta para pegar as informações do empréstimo
        cursor.execute("""
            SELECT usuarios.email, emprestimos.data_emprestimo, emprestimos.data_devolucao_prevista
            FROM emprestimos
            JOIN usuarios ON emprestimos.id_usuario = usuarios.id
            WHERE emprestimos.id_livro = ? AND emprestimos.status = 'ativo'
        """, (id_livro,))
        
        # Pegando o primeiro resultado
        emprestimo_info = cursor.fetchone()
        
    return emprestimo_info