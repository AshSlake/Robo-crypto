from decimal import Decimal


def calculate_jump_threshold(self, current_price, ma_fast_values, factor=1.5):
    """
    Calcula o jump_threshold baseado na volatilidade recente.

    Args:
        current_price (float): Preço atual do ativo.
        ma_fast_values (list): Lista de médias móveis rápidas recentes.
        factor (float): Fator de ajuste para o threshold. Padrão é 1.5.

    Returns:
        float: O valor calculado do jump_threshold.
    """
    if len(ma_fast_values) < 2:
        raise ValueError("Dados insuficientes para calcular jump_threshold.")

    # Calcular volatilidade recente como diferença percentual máxima entre médias móveis rápidas
    recent_volatility = max(ma_fast_values) - min(ma_fast_values)

    # Convertendo recent_volatility e current_price para Decimal
    recent_volatility = Decimal(recent_volatility)
    current_price = Decimal(current_price)

    # Calcular a volatilidade relativa (como porcentagem do preço atual)
    relative_volatility = recent_volatility / current_price

    # Definir o threshold como uma função da volatilidade recente
    jump_threshold = relative_volatility * Decimal(factor)
    return jump_threshold
