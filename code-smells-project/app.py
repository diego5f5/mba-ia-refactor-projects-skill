from flask import Flask
from flask_cors import CORS

from src.config.database import Database
from src.config.settings import ALLOWED_ORIGINS, DEBUG, HOST, PORT, SECRET_KEY
from src.middlewares.error_handler import register_error_handlers
from src.views.routes import register_routes


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = SECRET_KEY
    app.config["DEBUG"] = DEBUG

    CORS(app, origins=ALLOWED_ORIGINS)

    db = Database()
    db.get_connection()

    register_error_handlers(app)
    register_routes(app, db)

    return app


app = create_app()

if __name__ == "__main__":
    print("=" * 50)
    print("SERVIDOR INICIADO")
    print(f"Rodando em http://localhost:{PORT}")
    print("=" * 50)
    app.run(host=HOST, port=PORT, debug=DEBUG)
