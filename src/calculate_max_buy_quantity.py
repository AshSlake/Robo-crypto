import os
from decimal import Decimal, ROUND_DOWN
import logging
from binance.exceptions import BinanceAPIException

class QuantityCalculator:
    def __init__(self, client_binance, operation_code):
        self.client_binance = client_binance
        self.operation_code = operation_code

    def get_symbol_info(self):
        try:
            return self.client_binance.get_symbol_info(self.operation_code)
        except BinanceAPIException as e:
            logging.error(f"Erro ao obter informações do símbolo {self.operation_code}: {e}")
            raise  # Re-lance a exceção para que seja tratada pelo chamador.

    def calculate_max_buy_quantity(self, balance, current_price):
        if not isinstance(balance, (int, float, Decimal)) or balance <= 0:
            raise ValueError("O valor do balance deve ser um número positivo.")
        if not isinstance(current_price, (int, float, Decimal)) or current_price <= 0:
            raise ValueError("O valor do current_price deve ser um número positivo.")

        symbol_info = self.get_symbol_info()
        step_size = Decimal(symbol_info['filters'][0]['stepSize'])
        min_quantity = Decimal(symbol_info['filters'][0]['minQty'])

        max_quantity = Decimal(balance) / Decimal(current_price)
        max_quantity = max_quantity.quantize(step_size, rounding=ROUND_DOWN)
        max_quantity = max(min_quantity, max_quantity)

        logging.debug(f"Saldo: {balance}, Preço Atual: {current_price}, step_size: {step_size}, min_quantity: {min_quantity}, Quantidade Máxima Calculada: {max_quantity}")
        return max_quantity

    def calculate_max_sell_quantity(self, available_balance, current_price):
        if not isinstance(available_balance, (int, float, Decimal)) or available_balance <= 0:
            raise ValueError("O valor do available_balance deve ser um número positivo.")
        if not isinstance(current_price, (int, float, Decimal)) or current_price <= 0:
            raise ValueError("O valor do current_price deve ser um número positivo.")

        symbol_info = self.get_symbol_info()
        step_size = Decimal(symbol_info['filters'][0]['stepSize'])
        min_quantity = Decimal(symbol_info['filters'][0]['minQty'])
        min_notional = Decimal(symbol_info['filters'][1]['minNotional'])  # Assumindo que minNotional é o segundo filtro

        max_quantity = Decimal(available_balance)
        max_quantity = max_quantity.quantize(step_size, rounding=ROUND_DOWN)

        if (max_quantity * current_price) < min_notional:
            raise ValueError(f"Quantidade de venda resulta em valor inferior ao mínimo permitido: {min_notional}")

        max_quantity = max(min_quantity, max_quantity)

        logging.debug(f"Saldo Disponível: {available_balance}, Preço Atual: {current_price}, step_size: {step_size}, min_quantity: {min_quantity}, min_notional: {min_notional}, Quantidade Máxima de Venda Calculada: {max_quantity}")
        return max_quantity