def calculate_recent_growth_value(self, fast_gradients, growth_threshold, prev_ma_fast):
    """
    Calcula um valor representando o crescimento recente com base nos gradientes recentes.

    Args:
        fast_gradients (list): Lista de gradientes rápidos recentes.
        growth_threshold (float): Limiar de crescimento.
        prev_ma_fast (float): Média móvel rápida anterior.

    Returns:
        float: Valor calculado do crescimento recente.
    """
    # Média dos últimos 3 gradientes
    recent_average = sum(fast_gradients[-3:]) / 3

    # Calculando o valor do crescimento em função do limiar e da média anterior
    growth_value = recent_average - growth_threshold * prev_ma_fast

    return growth_value
