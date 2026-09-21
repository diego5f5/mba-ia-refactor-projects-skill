import logging

from flask import jsonify
from werkzeug.exceptions import HTTPException

logger = logging.getLogger("app")


def register_error_handlers(app):
    @app.errorhandler(HTTPException)
    def handle_http_exception(e):
        return jsonify({"erro": e.description, "sucesso": False}), e.code

    @app.errorhandler(Exception)
    def handle_unexpected_exception(e):
        logger.exception("Erro não tratado: %s", e)
        return jsonify({"erro": str(e), "sucesso": False}), 500
