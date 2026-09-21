from flask import Blueprint, jsonify

from src.controllers.pedido_controller import PedidoController
from src.controllers.produto_controller import ProdutoController
from src.controllers.usuario_controller import UsuarioController


def register_routes(app, db):
    produto_controller = ProdutoController(db)
    usuario_controller = UsuarioController(db)
    pedido_controller = PedidoController(db)

    produtos_bp = Blueprint("produtos", __name__)
    produtos_bp.add_url_rule("/produtos", "listar", produto_controller.listar, methods=["GET"])
    produtos_bp.add_url_rule("/produtos/busca", "buscar", produto_controller.buscar, methods=["GET"])
    produtos_bp.add_url_rule(
        "/produtos/<int:produto_id>", "buscar_por_id", produto_controller.buscar_por_id, methods=["GET"]
    )
    produtos_bp.add_url_rule("/produtos", "criar", produto_controller.criar, methods=["POST"])
    produtos_bp.add_url_rule(
        "/produtos/<int:produto_id>", "atualizar", produto_controller.atualizar, methods=["PUT"]
    )
    produtos_bp.add_url_rule(
        "/produtos/<int:produto_id>", "deletar", produto_controller.deletar, methods=["DELETE"]
    )

    usuarios_bp = Blueprint("usuarios", __name__)
    usuarios_bp.add_url_rule("/usuarios", "listar", usuario_controller.listar, methods=["GET"])
    usuarios_bp.add_url_rule(
        "/usuarios/<int:usuario_id>", "buscar_por_id", usuario_controller.buscar_por_id, methods=["GET"]
    )
    usuarios_bp.add_url_rule("/usuarios", "criar", usuario_controller.criar, methods=["POST"])
    usuarios_bp.add_url_rule("/login", "login", usuario_controller.login, methods=["POST"])

    pedidos_bp = Blueprint("pedidos", __name__)
    pedidos_bp.add_url_rule("/pedidos", "criar", pedido_controller.criar, methods=["POST"])
    pedidos_bp.add_url_rule("/pedidos", "listar_todos", pedido_controller.listar_todos, methods=["GET"])
    pedidos_bp.add_url_rule(
        "/pedidos/usuario/<int:usuario_id>",
        "listar_por_usuario",
        pedido_controller.listar_por_usuario,
        methods=["GET"],
    )
    pedidos_bp.add_url_rule(
        "/pedidos/<int:pedido_id>/status",
        "atualizar_status",
        pedido_controller.atualizar_status,
        methods=["PUT"],
    )

    relatorios_bp = Blueprint("relatorios", __name__)
    relatorios_bp.add_url_rule(
        "/relatorios/vendas", "vendas", pedido_controller.relatorio_vendas, methods=["GET"]
    )

    sistema_bp = Blueprint("sistema", __name__)

    @sistema_bp.route("/")
    def index():
        return jsonify(
            {
                "mensagem": "Bem-vindo à API da Loja",
                "versao": "1.0.0",
                "endpoints": {
                    "produtos": "/produtos",
                    "usuarios": "/usuarios",
                    "pedidos": "/pedidos",
                    "login": "/login",
                    "relatorios": "/relatorios/vendas",
                    "health": "/health",
                },
            }
        )

    @sistema_bp.route("/health")
    def health():
        cursor = db.get_connection().cursor()
        cursor.execute("SELECT COUNT(*) FROM produtos")
        produtos = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM usuarios")
        usuarios = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM pedidos")
        pedidos = cursor.fetchone()[0]
        return (
            jsonify(
                {
                    "status": "ok",
                    "database": "connected",
                    "counts": {"produtos": produtos, "usuarios": usuarios, "pedidos": pedidos},
                    "versao": "1.0.0",
                }
            ),
            200,
        )

    app.register_blueprint(produtos_bp)
    app.register_blueprint(usuarios_bp)
    app.register_blueprint(pedidos_bp)
    app.register_blueprint(relatorios_bp)
    app.register_blueprint(sistema_bp)
