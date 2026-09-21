from src.config.business_rules import CATEGORIAS_VALIDAS, NOME_PRODUTO_MAX, NOME_PRODUTO_MIN


def _row_to_dict(row):
    return {
        "id": row["id"],
        "nome": row["nome"],
        "descricao": row["descricao"],
        "preco": row["preco"],
        "estoque": row["estoque"],
        "categoria": row["categoria"],
        "ativo": row["ativo"],
        "criado_em": row["criado_em"],
    }


def get_todos(db):
    cursor = db.get_connection().cursor()
    cursor.execute("SELECT * FROM produtos")
    return [_row_to_dict(row) for row in cursor.fetchall()]


def get_por_id(db, produto_id):
    cursor = db.get_connection().cursor()
    cursor.execute("SELECT * FROM produtos WHERE id = ?", (produto_id,))
    row = cursor.fetchone()
    return _row_to_dict(row) if row else None


def buscar(db, termo, categoria=None, preco_min=None, preco_max=None):
    query = "SELECT * FROM produtos WHERE 1=1"
    params = []
    if termo:
        query += " AND (nome LIKE ? OR descricao LIKE ?)"
        params.extend([f"%{termo}%", f"%{termo}%"])
    if categoria:
        query += " AND categoria = ?"
        params.append(categoria)
    if preco_min is not None:
        query += " AND preco >= ?"
        params.append(preco_min)
    if preco_max is not None:
        query += " AND preco <= ?"
        params.append(preco_max)

    cursor = db.get_connection().cursor()
    cursor.execute(query, params)
    return [_row_to_dict(row) for row in cursor.fetchall()]


def criar(db, nome, descricao, preco, estoque, categoria):
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) VALUES (?, ?, ?, ?, ?)",
        (nome, descricao, preco, estoque, categoria),
    )
    conn.commit()
    return cursor.lastrowid


def atualizar(db, produto_id, nome, descricao, preco, estoque, categoria):
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE produtos SET nome = ?, descricao = ?, preco = ?, estoque = ?, categoria = ? WHERE id = ?",
        (nome, descricao, preco, estoque, categoria, produto_id),
    )
    conn.commit()
    return True


def deletar(db, produto_id):
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM produtos WHERE id = ?", (produto_id,))
    conn.commit()
    return True


def validar(dados):
    """Validação compartilhada entre criação e atualização (corrige a divergência encontrada na auditoria)."""
    erros = []

    if "nome" not in dados:
        erros.append("Nome é obrigatório")
    elif len(dados["nome"]) < NOME_PRODUTO_MIN:
        erros.append("Nome muito curto")
    elif len(dados["nome"]) > NOME_PRODUTO_MAX:
        erros.append("Nome muito longo")

    if "preco" not in dados:
        erros.append("Preço é obrigatório")
    elif dados["preco"] < 0:
        erros.append("Preço não pode ser negativo")

    if "estoque" not in dados:
        erros.append("Estoque é obrigatório")
    elif dados["estoque"] < 0:
        erros.append("Estoque não pode ser negativo")

    categoria = dados.get("categoria", "geral")
    if categoria not in CATEGORIAS_VALIDAS:
        erros.append(f"Categoria inválida. Válidas: {CATEGORIAS_VALIDAS}")

    return erros
