def calculate_moving_average(self, prices, window):
    """
    Calcula a média móvel simples (SMA) com base nos preços recentes.

    Args:
        prices (list): Lista de preços históricos.
        window (int): Tamanho da janela para o cálculo da média móvel.

    Returns:
        list: Lista de médias móveis calculadas para cada ponto onde há dados suficientes.
    """
    if len(prices) < window:
        raise ValueError(
            f"Dados insuficientes para calcular a média móvel. Necessário pelo menos {window} preços."
        )

    moving_averages = []
    for i in range(window - 1, len(prices)):
        # Calcula a média dos últimos "window" preços
        window_prices = prices[i - window + 1 : i + 1]
        moving_average = sum(window_prices) / window
        moving_averages.append(moving_average)

    return moving_averages
