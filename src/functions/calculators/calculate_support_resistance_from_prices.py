def calculate_support_resistance_from_prices(prices):
    """
    Calcula suporte e resistência a partir de uma lista de preços de fechamento.

    Args:
        prices (list): Lista de preços de fechamento recentes.

    Returns:
        dict: Dicionário com suporte e resistência.
    """
    if not prices or len(prices) == 0:
        raise ValueError("A lista de preços está vazia ou é inválida.")

    # Suporte: preço mais baixo
    support = min(prices)
    # Resistência: preço mais alto
    resistance = max(prices)

    return {
        "support": support,
        "resistance": resistance,
    }
