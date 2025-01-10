# calculate_quantity.py
import os 
from decimal import Decimal, ROUND_DOWN
import logging

class QuantityCalculator:
    def __init__(self, client_binance, operation_code):
        self.client_binance = client_binance
        self.operation_code = operation_code

    def calculate_max_buy_quantity(self, balance, current_price):
        symbol_info = self.client_binance.get_symbol_info(self.operation_code)
        step_size = min_quantity = Decimal('0')
        for filter in symbol_info['filters']:
            if filter['filterType'] == 'LOT_SIZE':
                step_size = Decimal(filter['stepSize'])
                min_quantity = Decimal(filter['minQty'])
                break

        if step_size == 0 or min_quantity == 0:
            raise ValueError("Invalid step size or min quantity.")

        max_quantity = Decimal(balance) / Decimal(current_price)
        max_quantity = max_quantity.quantize(step_size, rounding=ROUND_DOWN)
        max_quantity = max(min_quantity, max_quantity)

        logging.debug(f"Saldo: {balance}, Preço Atual: {current_price}, Quantidade Máxima Calculada: {max_quantity}")
        return max_quantity
