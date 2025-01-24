def detect_new_price_jump(self, fast_gradient, price_history, jump_threshold):
    """
    Detecta um novo salto no preço após uma correção.

    Args:
        fast_gradient (float): Gradiente rápido atual.
        price_history (list): Histórico de preços recentes.
        jump_threshold (float): Limiar de salto no preço.

    Returns:
        bool: Verdadeiro se houver um novo salto no preço.
    """
    if len(price_history) < 2:
        return False

    # Comparar o preço atual com o preço médio recente
    recent_average_price = sum(price_history[-3:]) / 3
    current_price = price_history[-1]

    # Detectar um salto significativo no preço
    return current_price > recent_average_price * jump_threshold
