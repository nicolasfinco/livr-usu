from flask import jsonify, request, Response,make_response
from main import app, con
from flask_bcrypt import generate_password_hash, check_password_hash
from funcao import validar_senha, cripytrografa, gerar_token, enviando_email
from fpdf import FPDF
from flask import send_file
import os
import pygal
import jwt
import bcrypt

import threading

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

@app.route('/livro', methods=['GET'])
def livro():
    token = request.cookies.get('access_token')

    if not token:
        return jsonify({'message': 'token necessario'}), 401

    try:
        payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])

    except jwt.ExpiredSignatureError:
        return jsonify({'message': 'token expirado'}), 401

    except jwt.InvalidTokenError:
        return jsonify({'message': 'token invalido'}), 401
    try:
        cur =con.cursor()
        cur.execute('SELECT id_livros, titulo, autor, ano_publicacao from livro')
        livros = cur.fetchall()
        livros_lista = []
        for livro in livros:
            livros_lista.append({
                'id_livros':livro[0]
                , 'titulo':livro[1]
                , 'autor':livro[2]
                , 'ano_publicacao':livro[3]
            })

        return jsonify(mensagem='lista de livros', livros=livros_lista)
    except Exception as e:
        return jsonify({"message": "deu ruim"}), 500
    finally:
        cur.close()

@app.route('/adicionar_livro', methods=['POST'])
def adicionar_livro():
    try:
        titulo = request.form.get('titulo')
        autor = request.form.get('autor')
        ano_publicacao = request.form.get('ano_publicacao')
        imagem = request.files.get('imagem')

        cursor = con.cursor()

        cursor.execute(
            "SELECT 1 FROM LIVRO WHERE TITULO = ?",
            (titulo,)
        )

        if cursor.fetchone():
            return jsonify(mensagem="JÁ TEM LIVRO COM ESSE NOME"), 400

        cursor.execute("""
            INSERT INTO LIVRO (TITULO, AUTOR, ANO_PUBLICACAO)
            VALUES (?, ?, ?) RETURNING id_livros
        """, (titulo, autor, ano_publicacao))

        codigo_livro = cursor.fetchone()[0]

        con.commit()

        caminho_imagem = None

        if imagem:
            nome_imagem = f"{codigo_livro}.jpg"
            caminho_imagem_destino = os.path.join(app.config['UPLOAD_FOLDER'], "Livros")
            os.makedirs(caminho_imagem_destino, exist_ok=True)
            caminho_imagem = os.path.join(caminho_imagem_destino, nome_imagem)
            imagem.save(caminho_imagem)

        return jsonify({
            'message': 'Livro cadastrado com sucesso',
            'livro': {
                'titulo': titulo,
                'autor': autor,
                'ano_publicacao': ano_publicacao
            }
        }), 201

        return jsonify(mensagem='Lista de livros', livro=livro_list)
    except Exception as e:
        return jsonify(mensagem=f"Erro ao consultar banco de dados: {e}"),500
    finally:
        cursor.close()


@app.route('/editar_livros/<int:id>', methods=['PUT'])
def editar_Livros(id):
    cur = con.cursor()
    cur.execute("""select id_livros, titulo, autor, ano_publicacao
                    from livro
                    where id_livros = ? """, (id,))
    tem_livro = cur.fetchone()
    if not tem_livro:
        cur.close()
        return jsonify({"error": "livro não encontrado"}), 404

    data = request.get_json()
    titulo = data.get('titulo')
    autor = data.get('autor')
    ano_publicacao = data.get('ano_publicacao')


    cur.execute(""" update livro set titulo = ?, autor = ?, ano_publicacao = ?
                where id_livros = ? """, (titulo, autor, ano_publicacao, id))
    con.commit()
    cur.close()

    return jsonify({'message': 'Livro autalizado com sucesso',
                    'livro':
                        {
                            'id_livro': id,
                            'titulo': titulo,
                            'autor': autor,
                            'ano_publicacao': ano_publicacao
                        }
                    })

@app.route('/deletar_livros/<int:id>', methods=['DELETE'])
def deletar_livros(id):
    cur = con.cursor()
    cur.execute("select 1 from livro where id_livros = ?", (id,))
    if not cur.fetchone():
        cur.close()
        return jsonify({"error": "livro nao encontrado"}), 404

    cur.execute("delete from livro where id_livros = ?", (id,))
    con.commit()
    cur.close()

    return jsonify(
        {
            "message": "Livro excluido com sucesso",
            'id_livro': id
        }
    )


@app.route('/usuario', methods=['GET'])
def usuario():
    try:
        cur = con.cursor()
        cur.execute('SELECT id_usuario, nome, usuario, senha FROM usuario')
        usuarios = cur.fetchall()

        usuarios_lista = []
        for u in usuarios:
            usuarios_lista.append({
                'id_usuario': u[0],
                'nome': u[1],
                'usuario': u[2],
                'senha': u[3]
            })

        return jsonify(mensagem='lista de usuarios', usuarios=usuarios_lista)

    except Exception as e:
        return jsonify({"message": "deu ruim"}), 500

    finally:
        cur.close()


@app.route('/adicionar_usuario', methods=['POST'])
def adicionar_usuario():
    dados = request.get_json()
    nome = dados.get('nome')
    usuario = dados.get('usuario')
    senha = dados.get('senha')

    if not validar_senha(senha):
        return jsonify({"error": "Senha fraca"}), 400
    senha_criptografada = cripytrografa(senha)

    cursor = con.cursor()

    cursor.execute(
        "SELECT 1 FROM USUARIO WHERE nome = ?",
        (nome,))
    if cursor.fetchone():
        return jsonify({"error": "Já existe usuário com esse nome"}), 400

    cursor.execute("""
        INSERT INTO USUARIO (NOME, USUARIO, SENHA)
        VALUES (?, ?, ?)
    """, (nome, usuario, senha_criptografada))

    con.commit()
    return jsonify({
        "message": "Usuário cadastrado com sucesso",
        "usuario": {
            "nome": nome,
            "usuario": usuario
        }
    }), 201

@app.route('/deletar_usuario/<int:id>', methods=['DELETE'])
def deletar_usuario(id):
    cur = con.cursor()
    cur.execute("select 1 from usuario where id_usuario = ?", (id,))
    if not cur.fetchone():
        cur.close()
        return jsonify({"error": "usuario nao encontrado"}), 404

    cur.execute("delete from usuario where id_usuario = ?", (id,))
    con.commit()
    cur.close()

    return jsonify(
        {
            "message": "usuario excluido com sucesso",
            'id_usuario': id
        }
    )

@app.route('/editar_usuario/<int:id>', methods=['PUT'])
def editar_usuario(id):
    cur = con.cursor()
    cur.execute("""select id_usuario, nome, usuario, senha
                    from usuario
                    where id_usuario = ? """, (id,))
    tem_usuario = cur.fetchone()
    if not tem_usuario:
        cur.close()
        return jsonify({"error": "usuario não encontrado"}), 404

    data = request.get_json()
    nome = data.get('nome')
    usuario = data.get('usuario')
    senha = data.get('senha')


    cur.execute(""" update usuario set nome = ?, usuario = ?, senha = ?
                where id_usuario = ? """, (nome, usuario, senha, id))
    con.commit()
    cur.close()

    return jsonify({'message': 'usuario autalizado com sucesso',
                    'usuario':
                        {
                            'id_usuario': id,
                            'nome': nome,
                            'usuario': usuario,
                            'senha': senha
                        }
                    })




@app.route('/login', methods=['POST'])
def login():

    dados = request.get_json()
    nome_usuario = dados.get('usuario')
    senha = dados.get('senha')

    cursor = con.cursor()

    cursor.execute("""
        SELECT ID_USUARIO, USUARIO, SENHA
        FROM USUARIO
        WHERE USUARIO = ?
    """, (nome_usuario,))

    usuario = cursor.fetchone()

    if not usuario:
        return jsonify({'mensagem': 'usuario ou senha invalida'}), 401

    senha_banco = usuario[2]
    id_usuario = usuario[0]

    if not check_password_hash(senha_banco, senha):
        return jsonify({'mensagem': 'usuario ou senha invalida'}), 401

    token = gerar_token(id_usuario)

    resposta = make_response(jsonify({'mensagem': 'login com sucesso'}), 200)

    resposta.set_cookie(
        'access_token',
        token,
        httponly=True,
        secure=False,
        samesite='Lax',
        path="/",
        max_age=3600
    )

    return resposta
# @app.route('/login', methods=['POST'])
# def login():
#     dados = request.get_json()
#
#     usuario = dados.get('usuario')
#     senha = dados.get('senha')
#
#     try:
#         cur = con.cursor()
#
#         cur.execute("select id_usuario, nome, usuario, senha from usuario where usuario = ?", (usuario,))
#         usuario_db = cur.fetchone()
#
#         if not usuario_db:
#             return jsonify({"message": "usuario ou senha invalido"}), 401
#
#         senha_dobanco = usuario_db[3]
#         id_usuario = usuario_db[0]
#
#         if not check_password_hash(senha_dobanco, senha):
#             return jsonify({"message": "usuario ou senha invalido"}), 401
#
#         token = gerar_token(id_usuario)
#
#         return jsonify({
#             "message": "login efetuado",
#             "token": token
#         })
#
#     except:
#         return jsonify({"message": "erro no login"}), 500

@app.route('/livros_relatorio', methods=['GET'])
def livros_relatorio():
    cursor = con.cursor()
    cursor.execute("SELECT id_livros, titulo, autor, ano_publicacao FROM livro")
    livros = cursor.fetchall()
    cursor.close()

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", style='B', size=16)
    pdf.cell(200, 10, "Relatorio de Livros", ln=True, align='C')
    pdf.ln(5)  # Espaço entre o título e a linha
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())  # Linha abaixo do título
    pdf.ln(5)  # Espaço após a linha
    pdf.set_font("Arial", size=12)
    for livro in livros:
        pdf.cell(200, 10, f"ID: {livro[0]} - {livro[1]} - {livro[2]} - {livro[3]}", ln=True)
    contador_livros = len(livros)
    pdf.ln(10)  # Espaço antes do contador
    pdf.set_font("Arial", style='B', size=12)
    pdf.cell(200, 10, f"Total de livros cadastrados: {contador_livros}", ln=True, align='C')
    pdf_path = "relatorio_livros.pdf"
    pdf.output(pdf_path)
    return send_file(pdf_path, as_attachment=True, mimetype='application/pdf')


@app.route('/usuario_relatorio', methods=['GET'])
def usuario_relatorio():
    cursor = con.cursor()
    cursor.execute("SELECT id_usuario, nome, usuario FROM usuario")
    usuario = cursor.fetchall()
    cursor.close()

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", style='B', size=16)
    pdf.cell(200, 10, "Relatorio de usuarios", ln=True, align='C')
    pdf.ln(5)  # Espaço entre o título e a linha
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())  # Linha abaixo do título
    pdf.ln(5)  # Espaço após a linha
    pdf.set_font("Arial", size=12)
    for usuario in usuario:
        pdf.cell(200, 10, f"ID: {usuario[0]} - {usuario[1]} - {usuario[2]}", ln=True)
    contador_usuario = len(usuario)
    pdf.ln(10)  # Espaço antes do contador
    pdf.set_font("Arial", style='B', size=12)
    pdf.cell(200, 10, f"Total de usuario cadastrados: {contador_usuario}", ln=True, align='C')
    pdf_path = "relatorio_usuario.pdf"
    pdf.output(pdf_path)
    return send_file(pdf_path, as_attachment=True, mimetype='application/pdf')


@app.route('/grafico', methods=['GET'])
def grafico():
    cur = con.cursor()
    cur.execute("""SELECT ano_publicacao, count(*)
                   FROM Livro
                   group by ano_publicacao
                   order by ano_publicacao
                """)
    resultado = cur.fetchall()
    cur.close()

    grafico = pygal.Bar()
    grafico._title = 'Quantidade de Livros por ano'

    for g in resultado:
        grafico.add(str(g[0]), g[1])
    return Response(grafico.render(), mimetype='image/svg+xml')

@app.route('/enviar_email', methods=['GET'])
def enviar_email():
    dados = request.json
    assunto = dados.get('assunto')
    mensagem = dados.get('mensagem')
    destinatario = dados.get('to')

    thread = threading.Thread(target=enviando_email,
                              args=(assunto, mensagem, destinatario))
    thread.start()

    return jsonify({'assunto': "enviado com sucesso!"})