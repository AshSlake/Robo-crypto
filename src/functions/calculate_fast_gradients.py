def calculate_fast_gradients(self, ma_fast_values):
    """
    Calcula os gradientes rápidos com base nos valores da média móvel rápida.

    Args:
        ma_fast_values (list): Lista de valores da média móvel rápida.

    Returns:
        list: Lista de gradientes rápidos calculados.
    """
    fast_gradients = []
    for i in range(1, len(ma_fast_values)):
        # Gradiente rápido é a variação percentual entre valores consecutivos de MA rápida
        gradient = ma_fast_values[i] - ma_fast_values[i - 1]
        fast_gradients.append(gradient)
    return fast_gradients
