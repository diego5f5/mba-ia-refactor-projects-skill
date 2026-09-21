import bcrypt


def _row_to_dict(row, incluir_senha=False):
    dado = {
        "id": row["id"],
        "nome": row["nome"],
        "email": row["email"],
        "tipo": row["tipo"],
        "criado_em": row["criado_em"],
    }
    if incluir_senha:
        dado["senha"] = row["senha"]
    return dado


def get_todos(db):
    cursor = db.get_connection().cursor()
    cursor.execute("SELECT * FROM usuarios")
    return [_row_to_dict(row) for row in cursor.fetchall()]


def get_por_id(db, usuario_id):
    cursor = db.get_connection().cursor()
    cursor.execute("SELECT * FROM usuarios WHERE id = ?", (usuario_id,))
    row = cursor.fetchone()
    return _row_to_dict(row) if row else None


def criar(db, nome, email, senha, tipo="cliente"):
    conn = db.get_connection()
    cursor = conn.cursor()
    senha_hash = bcrypt.hashpw(senha.encode(), bcrypt.gensalt()).decode()
    cursor.execute(
        "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
        (nome, email, senha_hash, tipo),
    )
    conn.commit()
    return cursor.lastrowid


def autenticar(db, email, senha):
    cursor = db.get_connection().cursor()
    cursor.execute("SELECT * FROM usuarios WHERE email = ?", (email,))
    row = cursor.fetchone()
    if row and bcrypt.checkpw(senha.encode(), row["senha"].encode()):
        return _row_to_dict(row)
    return None
