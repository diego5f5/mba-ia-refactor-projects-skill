import logging

from flask import current_app, jsonify

logger = logging.getLogger("admin")


class AdminController:
    def __init__(self, db):
        self.db = db

    def reset_database(self):
        if not current_app.config["DEBUG"]:
            return jsonify({"erro": "Disponível apenas em ambiente de desenvolvimento", "sucesso": False}), 403

        self.db.reset()
        logger.warning("Banco de dados resetado via /admin/reset-db")
        return jsonify({"mensagem": "Banco de dados resetado", "sucesso": True}), 200
