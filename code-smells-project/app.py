import logging

from flask import Flask
from flask_cors import CORS

from src.config.database import Database
from src.config.settings import ADMIN_TOKEN, ALLOWED_ORIGINS, DEBUG, HOST, PORT, SECRET_KEY
from src.middlewares.error_handler import register_error_handlers
from src.views.routes import register_routes

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s [%(name)s] %(message)s")
logger = logging.getLogger("app")


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = SECRET_KEY
    app.config["DEBUG"] = DEBUG
    app.config["ADMIN_TOKEN"] = ADMIN_TOKEN

    CORS(app, origins=ALLOWED_ORIGINS)

    db = Database()
    db.get_connection()

    register_error_handlers(app)
    register_routes(app, db)

    return app


app = create_app()

if __name__ == "__main__":
    logger.info("Servidor iniciado em http://localhost:%s", PORT)
    app.run(host=HOST, port=PORT, debug=DEBUG)
