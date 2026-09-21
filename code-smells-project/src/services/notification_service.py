import logging

logger = logging.getLogger("notifications")


def notificar_pedido_criado(pedido_id, usuario_id):
    logger.info("Pedido %s criado para usuário %s: disparar email/sms/push", pedido_id, usuario_id)


def notificar_status_pedido(pedido_id, novo_status):
    if novo_status == "aprovado":
        logger.info("Pedido %s aprovado, preparar envio", pedido_id)
    elif novo_status == "cancelado":
        logger.info("Pedido %s cancelado, devolver estoque", pedido_id)
