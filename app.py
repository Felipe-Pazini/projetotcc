from flask import Flask, render_template, jsonify, request
import mysql.connector

app = Flask(__name__)

def conectar_banco():
    return mysql.connector.connect(
        host="host.docker.internal", 
        user="root",
        password="172909",
        database="almoxarifado"
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
            "estoque": "/api/estoque (GET/POST)"
        }
    })

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