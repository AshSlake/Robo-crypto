def calculate_gradient_increase_percentage(current_gradient, previous_gradient):
    """
    Calcula a porcentagem de aumento do gradiente atual em relação ao gradiente anterior.

    Args:
        current_gradient (float): O gradiente atual.
        previous_gradient (float): O gradiente anterior.

    Returns:
        float: Porcentagem de aumento do gradiente atual em relação ao anterior.
               Retorna 0 se o gradiente anterior for 0.
    """
    if previous_gradient == 0:
        return (
            0  # Evitar divisão por zero e retornar 0 em caso de gradiente anterior nulo
        )

    # Calcula a porcentagem de aumento
    percentage_increase = (
        (current_gradient - previous_gradient) / abs(previous_gradient)
    ) * 100
    return percentage_increase
