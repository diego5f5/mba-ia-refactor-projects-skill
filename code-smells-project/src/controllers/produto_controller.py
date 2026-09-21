from flask import jsonify, request

from src.models import produto_model


class ProdutoController:
    def __init__(self, db):
        self.db = db

    def listar(self):
        produtos = produto_model.get_todos(self.db)
        return jsonify({"dados": produtos, "sucesso": True}), 200

    def buscar_por_id(self, produto_id):
        produto = produto_model.get_por_id(self.db, produto_id)
        if not produto:
            return jsonify({"erro": "Produto não encontrado", "sucesso": False}), 404
        return jsonify({"dados": produto, "sucesso": True}), 200

    def buscar(self):
        termo = request.args.get("q", "")
        categoria = request.args.get("categoria")
        preco_min = request.args.get("preco_min", type=float)
        preco_max = request.args.get("preco_max", type=float)
        resultados = produto_model.buscar(self.db, termo, categoria, preco_min, preco_max)
        return jsonify({"dados": resultados, "total": len(resultados), "sucesso": True}), 200

    def criar(self):
        dados = request.get_json(silent=True) or {}
        erros = produto_model.validar(dados)
        if erros:
            return jsonify({"erro": erros[0], "erros": erros}), 400

        produto_id = produto_model.criar(
            self.db,
            dados["nome"],
            dados.get("descricao", ""),
            dados["preco"],
            dados["estoque"],
            dados.get("categoria", "geral"),
        )
        return jsonify({"dados": {"id": produto_id}, "sucesso": True, "mensagem": "Produto criado"}), 201

    def atualizar(self, produto_id):
        if not produto_model.get_por_id(self.db, produto_id):
            return jsonify({"erro": "Produto não encontrado"}), 404

        dados = request.get_json(silent=True) or {}
        erros = produto_model.validar(dados)
        if erros:
            return jsonify({"erro": erros[0], "erros": erros}), 400

        produto_model.atualizar(
            self.db,
            produto_id,
            dados["nome"],
            dados.get("descricao", ""),
            dados["preco"],
            dados["estoque"],
            dados.get("categoria", "geral"),
        )
        return jsonify({"sucesso": True, "mensagem": "Produto atualizado"}), 200

    def deletar(self, produto_id):
        if not produto_model.get_por_id(self.db, produto_id):
            return jsonify({"erro": "Produto não encontrado"}), 404

        produto_model.deletar(self.db, produto_id)
        return jsonify({"sucesso": True, "mensagem": "Produto deletado"}), 200
