from decimal import Decimal
from functions.logger import bot_logger


def calculate_profit(entry_price, quantity, current_price):
    """Calcula o lucro ou prejuízo de uma posição.

    Args:
        entry_price (Decimal): Preço de entrada da posição.
        quantity (Decimal): Quantidade do ativo.
        current_price (Decimal): Preço atual do ativo.

    Returns:
        Decimal: Lucro (positivo) ou prejuízo (negativo) em USDT.  Retorna None se entry_price for None
    """
    if entry_price is None:
        return None
    if current_price is not Decimal:
        current_price = Decimal(current_price)
    if entry_price is not Decimal:
        entry_price = Decimal(entry_price)
    profit_per_unit = current_price - entry_price
    total_profit = profit_per_unit * quantity
    return total_profit


def log_profit(entry_price, quantity, current_price):
    profit = calculate_profit(entry_price, quantity, current_price)
    if profit is not None:
        symbol = "+" if profit >= 0 else "-"
        bot_logger.info(f"Lucro/Prejuízo da operação: {symbol}{abs(profit):.8f} USDT")
