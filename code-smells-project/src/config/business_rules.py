"""Constantes de regra de negócio extraídas do código (elimina magic numbers)."""

NOME_PRODUTO_MIN = 2
NOME_PRODUTO_MAX = 200

CATEGORIAS_VALIDAS = ["informatica", "moveis", "vestuario", "geral", "eletronicos", "livros"]

STATUS_PEDIDO_VALIDOS = ["pendente", "aprovado", "enviado", "entregue", "cancelado"]

DESCONTO_FAIXA_ALTA = (10000, 0.10)
DESCONTO_FAIXA_MEDIA = (5000, 0.05)
DESCONTO_FAIXA_BAIXA = (1000, 0.02)


def calcular_desconto(faturamento):
    limite, taxa = DESCONTO_FAIXA_ALTA
    if faturamento > limite:
        return faturamento * taxa
    limite, taxa = DESCONTO_FAIXA_MEDIA
    if faturamento > limite:
        return faturamento * taxa
    limite, taxa = DESCONTO_FAIXA_BAIXA
    if faturamento > limite:
        return faturamento * taxa
    return 0
