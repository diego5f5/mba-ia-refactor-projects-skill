from flask import jsonify, request

from src.config.business_rules import STATUS_PEDIDO_VALIDOS
from src.models import pedido_model
from src.services import notification_service


def _validar_itens(itens):
    """Valida a forma de cada item antes de tocar no banco (achado da revisão pós-auditoria)."""
    for item in itens:
        if not isinstance(item, dict) or "produto_id" not in item or "quantidade" not in item:
            return "Cada item deve conter produto_id e quantidade"
        if not isinstance(item["produto_id"], int):
            return "produto_id deve ser um número inteiro"
        if not isinstance(item["quantidade"], int) or item["quantidade"] <= 0:
            return "quantidade deve ser um número inteiro maior que zero"
    return None


class PedidoController:
    def __init__(self, db):
        self.db = db

    def criar(self):
        dados = request.get_json(silent=True) or {}
        usuario_id = dados.get("usuario_id")
        itens = dados.get("itens", [])

        if not usuario_id:
            return jsonify({"erro": "Usuario ID é obrigatório"}), 400
        if not itens:
            return jsonify({"erro": "Pedido deve ter pelo menos 1 item"}), 400

        erro_itens = _validar_itens(itens)
        if erro_itens:
            return jsonify({"erro": erro_itens}), 400

        resultado = pedido_model.criar(self.db, usuario_id, itens)
        if "erro" in resultado:
            return jsonify({"erro": resultado["erro"], "sucesso": False}), 400

        notification_service.notificar_pedido_criado(resultado["pedido_id"], usuario_id)
        return jsonify({"dados": resultado, "sucesso": True, "mensagem": "Pedido criado com sucesso"}), 201

    def listar_por_usuario(self, usuario_id):
        pedidos = pedido_model.get_por_usuario(self.db, usuario_id)
        return jsonify({"dados": pedidos, "sucesso": True}), 200

    def listar_todos(self):
        pedidos = pedido_model.get_todos(self.db)
        return jsonify({"dados": pedidos, "sucesso": True}), 200

    def atualizar_status(self, pedido_id):
        dados = request.get_json(silent=True) or {}
        novo_status = dados.get("status", "")

        if novo_status not in STATUS_PEDIDO_VALIDOS:
            return jsonify({"erro": "Status inválido"}), 400

        pedido_model.atualizar_status(self.db, pedido_id, novo_status)
        notification_service.notificar_status_pedido(pedido_id, novo_status)
        return jsonify({"sucesso": True, "mensagem": "Status atualizado"}), 200

    def relatorio_vendas(self):
        relatorio = pedido_model.relatorio_vendas(self.db)
        return jsonify({"dados": relatorio, "sucesso": True}), 200
