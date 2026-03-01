from flask import Flask, render_template, request, redirect
import sqlite3
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)

UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


def conectar():
    return sqlite3.connect("banco.db")


def criar_tabela():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT,
            categoria TEXT,
            quantidade INTEGER,
            imagem TEXT,
            retiradas INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()


# ===== CLIENTE =====
@app.route("/")
def index():
	busca = request.args.get("busca","") 
	
	conn = conectar() 
	cursor = conn.cursor() 
	
	if busca: 
		cursor.execute("""
			SELECT * FROM produtos
			WHERE LOWER(nome) LIKE LOWER(?) 
			OR LOWER(categoria) LIKE LOWER(?)
			ORDER BY categoria 
		""",('%'+busca+'%','%'+busca+'%')) 

	
	else:
		cursor.execute("SELECT * FROM produtos ORDER BY categoria") 
	
	
	produtos = cursor.fetchall() 
	conn.close() 
	
	return render_template("index.html",produtos=produtos,busca=busca)
	
	
	


# ===== ADMIN =====
@app.route("/admin")
def admin():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM produtos")
    produtos = cursor.fetchall()
    conn.close()
    return render_template("admin.html", produtos=produtos)


# ===== ADICIONAR =====
@app.route("/adicionar", methods=["GET","POST"])
def adicionar():

    if request.method == "POST":
        nome = request.form["nome"]
        categoria = request.form["categoria"]
        quantidade = request.form["quantidade"]
        arquivo = request.files["imagem"]

        nome_arquivo = ""
        if arquivo and arquivo.filename != "":
            nome_arquivo = secure_filename(arquivo.filename)
            caminho = os.path.join(app.config["UPLOAD_FOLDER"], nome_arquivo)
            arquivo.save(caminho)

        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO produtos (nome,categoria,quantidade,imagem)
            VALUES (?,?,?,?)
        """,(nome,categoria,quantidade,nome_arquivo))
        conn.commit()
        conn.close()

        return redirect("/admin")

    return render_template("adicionar.html")


# ===== DIMINUIR =====
@app.route("/diminuir/<int:id>")
def diminuir(id):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE produtos
        SET quantidade = CASE WHEN quantidade>0 THEN quantidade-1 ELSE 0 END,
            retiradas = retiradas + 1
        WHERE id=?
    """,(id,))

    conn.commit()
    conn.close()
    return redirect("/")


# ===== REMOVER =====
@app.route("/remover/<int:id>")
def remover(id):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM produtos WHERE id=?",(id,))
    conn.commit()
    conn.close()
    return redirect("/admin")


# ===== GRÁFICOS =====
@app.route("/grafico")
def grafico():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT nome, retiradas FROM produtos ORDER BY retiradas DESC")
    dados = cursor.fetchall()
    conn.close()
    return render_template("grafico.html", dados=dados)

def iniciar_banco():
	conn = conectar()
	cursor = conn.cursor() 
	cursor.execute(""" 
		CREATE TABLE IF NOT EXISTS produtos (
			id INTEGER PRIMARY KEY AUTOINCREMENT,
			nome TEXT,
			categoria TEXT,
			quantidade INTEGER,
			imagem TEXT,
			retiradas INTEGER DEFAULT 0
		)
		""")
	
	conn.commit() 
	conn.close() 


# ==== EDITAR PRODUTOS ====

@app.route("/editar/<int:id>",methods=["GET","POST"])
def editar(id):
	conn = conectar() 
	cursor = conn.cursor() 
	
	if request.method == "POST":
		nome = request.form["nome"]
		categoria = request.form["categoria"]
		quantidade = request.form["quantidade"]
		
		cursor.execute("""
			UPDATE produtos 
			SET nome=?, categoria=?,quantidade=?
			WHERE id=?
		
		""",(nome,categoria,quantidade,id))
		
		conn.commit()
		conn.close()
		return redirect("/admin") 
	
	cursor.execute("SELECT * FROM produtos WHERE id=?",(id,)) 
	produto = cursor.fetchone()
	conn.close()
	
	return render_template("editar.html",produto=produto)


@app.route("/dashboard") 

def dashboard():
	conn = conectar() 
	cursor = conn.cursor() 
	
	cursor.execute("SELECT COUNT(*) FROM produtos") 
	total_produtos = cursor.fetchone()[0]
	
	cursor.execute("SELECT SUM(quantidade) FROM produtos")
	total_itens = cursor.fetchone()[0] or 0 
	
	cursor.execute("SELECT SUM(retiradas) FROM produtos")
	
	total_retiradas = cursor.fetchone()[0] or 0 
	
	conn.close() 
	
	return render_template("dashboard.html",total_produtos=total_produtos,total_itens=total_itens,total_retiradas=total_retiradas)


iniciar_banco()


if __name__ == "__main__":
    criar_tabela()
    app.run(debug=True)
