def calculate_gradient_percentage_change(current_gradient, previous_gradient):
    """
    Calcula a porcentagem de aumento ou queda do gradiente atual em relação ao gradiente anterior.

    Args:
        current_gradient (float): O gradiente atual.
        previous_gradient (float): O gradiente anterior.

    Returns:
        tuple: (percentage_increase, percentage_decrease)
            - percentage_increase (float): Porcentagem de aumento do gradiente.
            - percentage_decrease (float): Porcentagem de queda do gradiente.
              Ambos retornam 0 se o gradiente anterior for 0.
    """
    if previous_gradient == 0:
        # Evitar divisão por zero, retornando 0 para ambas as porcentagens
        return 0, 0

    # Calcula a porcentagem de mudança
    percentage_change = (
        (current_gradient - previous_gradient) / abs(previous_gradient)
    ) * 100

    if percentage_change > 0:
        # Se o gradiente atual é maior, é um aumento
        return percentage_change, 0
    else:
        # Se o gradiente atual é menor, é uma queda
        return 0, abs(percentage_change)
