import os
from flask import Flask, render_template, jsonify, request
from flask_bcrypt import Bcrypt  # Importa o Bcrypt
import mysql.connector

app = Flask(__name__)
bcrypt = Bcrypt(app)  # Inicializa o Bcrypt no Flask

def conectar_banco():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "host.docker.internal"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME", "almoxarifado"),
    )


@app.route("/")
def index():
    return render_template("index.html")

@app.route("/home")
def home():
    return render_template("home.html")

@app.route("/cadastro")
def cadastro():
    return render_template("cadastro.html")

@app.route("/estoque")
def estoque():
    return render_template("estoque.html")


############################## Rotas da API

@app.route("/api", methods=["GET"])
def api_info():
    return jsonify({
        "mensagem": "Bem-vindo à API do Almoxarifado!",
        "status": "online",
        "endpoints": {
            "estoque": "/api/estoque (GET/POST)",
            "usuarios_cadastro": "/api/usuarios (POST)",
            "usuarios_login": "/api/login (POST)"
        }
    })
############################################ Api

# --- NOVA ROTA: Cadastro de Usuário com Bcrypt ---
@app.route("/api/usuarios", methods=["POST"])
def cadastrar_usuario():
    dados = request.get_json()
    nome = dados.get("nome")
    email = dados.get("email")
    senha = dados.get("senha")

    if not nome or not email or not senha:
        return jsonify({"sucesso": False, "erro": "Todos os campos (nome, email, senha) são obrigatórios!"}), 400

    # Gera o hash da senha usando Bcrypt (transforma em string decodificada em utf-8 para salvar no banco)
    senha_criptografada = bcrypt.generate_password_hash(senha).decode('utf-8')

    try:
        conexao = conectar_banco()
        cursor = conexao.cursor()
        
        sql = "INSERT INTO usuarios (nome, email, senha) VALUES (%s, %s, %s)"
        valores = (nome, email, senha_criptografada)
        
        cursor.execute(sql, valores)
        conexao.commit()
        cursor.close()
        conexao.close()
        
        return jsonify({"sucesso": True, "mensagem": "Usuário cadastrado com sucesso!"}), 201
    except mysql.connector.Error as err:
        if err.errno == 1062:  # Erro de entrada duplicada para o email UNIQUE
            return jsonify({"sucesso": False, "erro": "Este e-mail já está cadastrado!"}), 400
        return jsonify({"sucesso": False, "erro": str(err)}), 500

############################################  Api
@app.route("/api/login", methods=["POST"])
def login_usuario():
    dados = request.get_json()
    email = dados.get("email")
    senha = dados.get("senha")

    if not email or not senha:
        return jsonify({"sucesso": False, "erro": "E-mail e senha são obrigatórios!"}), 400

    try:
        conexao = conectar_banco()
        cursor = conexao.cursor(dictionary=True)
        
        # Busca o usuário pelo e-mail
        cursor.execute("SELECT * FROM usuarios WHERE email = %s", (email,))
        usuario = cursor.fetchone()
        
        cursor.close()
        conexao.close()

        # Se o usuário existe, o Bcrypt compara a senha digitada com o hash do banco
        if usuario and bcrypt.check_password_hash(usuario['senha'], senha):
            return jsonify({
                "sucesso": True, 
                "mensagem": "Login realizado com sucesso!",
                "usuario": {
                    "id": usuario['id'],
                    "nome": usuario['nome'],
                    "email": usuario['email']
                }
            }), 200
        else:
            return jsonify({"sucesso": False, "erro": "E-mail ou senha incorretos!"}), 401

    except Exception as e:
        return jsonify({"sucesso": False, "erro": str(e)}), 500


############################################ Api
@app.route("/api/estoque", methods=["GET"])
def listar_estoque():
    try:
        conexao = conectar_banco()
        cursor = conexao.cursor(dictionary=True) 
        cursor.execute("SELECT * FROM produtos")
        itens = cursor.fetchall()
        cursor.close()
        conexao.close()
        return jsonify({"sucesso": True, "dados": itens}), 200
    except Exception as e:
        return jsonify({"sucesso": False, "erro": str(e)}), 500

@app.route("/api/estoque", methods=["POST"])
def adicionar_item_estoque():
    dados = request.get_json()
    nome = dados.get("nome")
    quantidade = dados.get("quantidade")
    preco = dados.get("preco")

    if not nome or quantidade is None:
        return jsonify({"sucesso": False, "erro": "Campos 'nome' e 'quantidade' são obrigatórios!"}), 400

    try:
        conexao = conectar_banco()
        cursor = conexao.cursor()
        sql = "INSERT INTO produtos (nome, quantidade, preco) VALUES (%s, %s, %s)"
        valores = (nome, quantidade, preco)
        cursor.execute(sql, valores)
        conexao.commit()
        cursor.close()
        conexao.close()
        return jsonify({"sucesso": True, "mensagem": "Item cadastrado com sucesso!"}), 201
    except Exception as e:
        return jsonify({"sucesso": False, "erro": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
