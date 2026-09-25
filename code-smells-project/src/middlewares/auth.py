import hmac
from functools import wraps

from flask import current_app, jsonify, request


def require_admin(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        expected = current_app.config.get("ADMIN_TOKEN", "")
        provided = request.headers.get("Authorization", "").removeprefix("Bearer ").strip()
        # Sem ADMIN_TOKEN configurado a rota fica bloqueada (falha fechada)
        if not expected or not hmac.compare_digest(provided, expected):
            return jsonify({"erro": "Não autorizado", "sucesso": False}), 401
        return view(*args, **kwargs)

    return wrapper
