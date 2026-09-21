import logging

from flask import jsonify
from werkzeug.exceptions import HTTPException

logger = logging.getLogger('app')


def register_error_handlers(app):
    @app.errorhandler(HTTPException)
    def handle_http_exception(e):
        return jsonify({'error': e.description}), e.code

    @app.errorhandler(Exception)
    def handle_unexpected_exception(e):
        logger.exception('Erro não tratado: %s', e)
        return jsonify({'error': str(e)}), 500
