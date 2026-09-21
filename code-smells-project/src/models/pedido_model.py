from src.config.business_rules import STATUS_PEDIDO_VALIDOS, calcular_desconto


def _montar_pedidos(db, where_clause, params):
    """Monta pedidos + itens em no máximo 2 queries, eliminando o N+1 do código original."""
    cursor = db.get_connection().cursor()
    cursor.execute(f"SELECT * FROM pedidos WHERE {where_clause}", params)
    pedidos_rows = cursor.fetchall()

    pedidos = {
        row["id"]: {
            "id": row["id"],
            "usuario_id": row["usuario_id"],
            "status": row["status"],
            "total": row["total"],
            "criado_em": row["criado_em"],
            "itens": [],
        }
        for row in pedidos_rows
    }

    if not pedidos:
        return list(pedidos.values())

    pedido_ids = list(pedidos.keys())
    placeholders = ",".join("?" for _ in pedido_ids)
    cursor.execute(
        f"""
        SELECT ip.pedido_id, ip.produto_id, ip.quantidade, ip.preco_unitario, p.nome AS produto_nome
        FROM itens_pedido ip
        LEFT JOIN produtos p ON p.id = ip.produto_id
        WHERE ip.pedido_id IN ({placeholders})
        """,
        pedido_ids,
    )
    for row in cursor.fetchall():
        pedidos[row["pedido_id"]]["itens"].append(
            {
                "produto_id": row["produto_id"],
                "produto_nome": row["produto_nome"] or "Desconhecido",
                "quantidade": row["quantidade"],
                "preco_unitario": row["preco_unitario"],
            }
        )

    return list(pedidos.values())


def get_por_usuario(db, usuario_id):
    return _montar_pedidos(db, "usuario_id = ?", (usuario_id,))


def get_todos(db):
    return _montar_pedidos(db, "1 = 1", ())


def criar(db, usuario_id, itens):
    conn = db.get_connection()
    cursor = conn.cursor()

    total = 0
    produtos_cache = {}
    for item in itens:
        cursor.execute("SELECT * FROM produtos WHERE id = ?", (item["produto_id"],))
        produto = cursor.fetchone()
        if produto is None:
            return {"erro": f"Produto {item['produto_id']} não encontrado"}
        if produto["estoque"] < item["quantidade"]:
            return {"erro": f"Estoque insuficiente para {produto['nome']}"}
        produtos_cache[item["produto_id"]] = produto
        total += produto["preco"] * item["quantidade"]

    cursor.execute(
        "INSERT INTO pedidos (usuario_id, status, total) VALUES (?, 'pendente', ?)",
        (usuario_id, total),
    )
    pedido_id = cursor.lastrowid

    for item in itens:
        produto = produtos_cache[item["produto_id"]]
        cursor.execute(
            "INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario) VALUES (?, ?, ?, ?)",
            (pedido_id, item["produto_id"], item["quantidade"], produto["preco"]),
        )
        cursor.execute(
            "UPDATE produtos SET estoque = estoque - ? WHERE id = ?",
            (item["quantidade"], item["produto_id"]),
        )

    conn.commit()
    return {"pedido_id": pedido_id, "total": total}


def atualizar_status(db, pedido_id, novo_status):
    if novo_status not in STATUS_PEDIDO_VALIDOS:
        return False
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE pedidos SET status = ? WHERE id = ?", (novo_status, pedido_id))
    conn.commit()
    return True


def relatorio_vendas(db):
    cursor = db.get_connection().cursor()

    cursor.execute("SELECT COUNT(*) FROM pedidos")
    total_pedidos = cursor.fetchone()[0]

    cursor.execute("SELECT SUM(total) FROM pedidos")
    faturamento = cursor.fetchone()[0] or 0

    cursor.execute("SELECT COUNT(*) FROM pedidos WHERE status = 'pendente'")
    pendentes = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM pedidos WHERE status = 'aprovado'")
    aprovados = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM pedidos WHERE status = 'cancelado'")
    cancelados = cursor.fetchone()[0]

    desconto = calcular_desconto(faturamento)

    return {
        "total_pedidos": total_pedidos,
        "faturamento_bruto": round(faturamento, 2),
        "desconto_aplicavel": round(desconto, 2),
        "faturamento_liquido": round(faturamento - desconto, 2),
        "pedidos_pendentes": pendentes,
        "pedidos_aprovados": aprovados,
        "pedidos_cancelados": cancelados,
        "ticket_medio": round(faturamento / total_pedidos, 2) if total_pedidos > 0 else 0,
    }
