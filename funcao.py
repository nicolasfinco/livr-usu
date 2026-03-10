from flask_bcrypt import generate_password_hash
from main import app
import smtplib
from email.mime.text import MIMEText
import jwt
import datetime



def validar_senha(senha):

    maiuscula = minuscula = numero = caracterpcd = oito = False

    if len(senha) >= 8:
        oito = True

    for s in senha:
        if s.isupper():
            maiuscula = True
        if s.islower():
            minuscula = True
        if s.isdigit():
            numero = True
        if not s.isalnum():
            caracterpcd = True

    if (oito and maiuscula and minuscula and numero and caracterpcd):
        return True

    return False

def cripytrografa(senha):
    return generate_password_hash(senha).decode('utf-8')

def autenticar_usuario(con, usuario, senha):
    cursor = con.cursor()

    try:
        cursor.execute("""
            SELECT usuario, senha
            FROM usuario
            WHERE usuario = ?
        """, (usuario,))

        dados = cursor.fetchone()

        if not dados:
            return {"erro": "Usuário não encontrado"}, 404

        # dados[1] = senha criptografada
        if senha(dados[1], senha):
            return {
                "mensagem": "Login realizado com sucesso",
                "usuario": dados[0]
            }, 200

        return {"erro": "Usuário ou senha inválidos"}, 401

    finally:
        cursor.close()

def enviando_email(destinatario, assunto, mensagem):
    user = 'Lais@prossora'
    senha = 'zfhl glqx qyuv ovzx'

    msg = MIMEText(mensagem)
    msg['From'] = user
    msg['To'] = destinatario
    msg['Subject'] = assunto

    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(user, senha)
    server.send_message(msg)
    server.quit()

def gerar_token(id_usuario):
    payload = {
        'id_usuario': id_usuario,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=30)
    }

    token = jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')
    return token


def remover_bearer(token):
    if token.startswith('Bearer '):
        return token[len('Bearer '):]
    return token