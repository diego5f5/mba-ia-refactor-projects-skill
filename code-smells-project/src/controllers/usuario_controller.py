from flask import jsonify, request

from src.models import usuario_model


class UsuarioController:
    def __init__(self, db):
        self.db = db

    def listar(self):
        usuarios = usuario_model.get_todos(self.db)
        return jsonify({"dados": usuarios, "sucesso": True}), 200

    def buscar_por_id(self, usuario_id):
        usuario = usuario_model.get_por_id(self.db, usuario_id)
        if not usuario:
            return jsonify({"erro": "Usuário não encontrado"}), 404
        return jsonify({"dados": usuario, "sucesso": True}), 200

    def criar(self):
        dados = request.get_json(silent=True) or {}
        nome = dados.get("nome", "")
        email = dados.get("email", "")
        senha = dados.get("senha", "")

        if not nome or not email or not senha:
            return jsonify({"erro": "Nome, email e senha são obrigatórios"}), 400

        usuario_id = usuario_model.criar(self.db, nome, email, senha)
        return jsonify({"dados": {"id": usuario_id}, "sucesso": True}), 201

    def login(self):
        dados = request.get_json(silent=True) or {}
        email = dados.get("email", "")
        senha = dados.get("senha", "")

        if not email or not senha:
            return jsonify({"erro": "Email e senha são obrigatórios"}), 400

        usuario = usuario_model.autenticar(self.db, email, senha)
        if not usuario:
            return jsonify({"erro": "Email ou senha inválidos", "sucesso": False}), 401

        return jsonify({"dados": usuario, "sucesso": True, "mensagem": "Login OK"}), 200
