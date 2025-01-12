import os
from decimal import Decimal, ROUND_DOWN , ROUND_UP
from logger import bot_logger, erro_logger
from binance.exceptions import BinanceAPIException

class QuantityCalculator:
    def __init__(self, client_binance, operation_code):
        self.client_binance = client_binance
        self.operation_code = operation_code

    def calculate_max_buy_quantity(self, symbol_info, balance, current_price):
      if not isinstance(balance, (int, float, Decimal)) or balance <= 0:
        raise ValueError("O valor do balance deve ser um número positivo.")
      if not isinstance(current_price, (int, float, Decimal)) or current_price <= 0:
        raise ValueError("O valor do current_price deve ser um número positivo.")

      # Inicializando as variáveis
      step_size = None
      min_quantity = None
      min_notional = None

      # Itera pelos filtros para encontrar LOT_SIZE e NOTIONAL
      for filter in symbol_info['filters']:
        if filter['filterType'] == 'LOT_SIZE':
            step_size = Decimal(filter['stepSize'])
            min_quantity = Decimal(filter['minQty'])
        if filter['filterType'] == 'NOTIONAL':
            min_notional = Decimal(filter['minNotional'])

      # Verifica se step_size, min_quantity ou min_notional não foram encontrados
      if step_size is None or min_quantity is None or min_notional is None:
        raise ValueError("Não foi possível encontrar 'stepSize', 'minQty' ou 'minNotional'.")

      # Calcula a quantidade mínima para o notional:
      min_quantity_notional = (Decimal(min_notional) / Decimal(current_price)).quantize(step_size, rounding=ROUND_UP)

      # Calcula a quantidade máxima teórica (sem restrições):
      max_quantity_temp = Decimal(balance) / Decimal(current_price)

      # Ajusta a quantidade máxima para baixo, respeitando o step_size:
      max_quantity = max_quantity_temp.quantize(step_size, rounding=ROUND_DOWN)

      # Garante que max_quantity atende ao min_notional, ajustando em incrementos de step_size se necessário:
      while max_quantity * Decimal(current_price) < Decimal(min_notional):
        max_quantity += step_size


      # Garante que a quantidade respeita min_quantity
      max_quantity = max(min_quantity, max_quantity)

      bot_logger.info(f"Saldo: {balance}, Preço Atual: {current_price}, step_size: {step_size}, min_quantity: {min_quantity}, min_notional: {min_notional}, Quantidade Máxima Calculada: {max_quantity}")
      return max_quantity


    from decimal import Decimal, ROUND_DOWN, ROUND_UP

    from decimal import Decimal, ROUND_DOWN, ROUND_UP

    def calculate_max_sell_quantity(self, symbol_info, available_balance, current_price):
      if not isinstance(available_balance, (int, float, Decimal)) or available_balance <= 0:
        raise ValueError("O valor do available_balance deve ser um número positivo.")
      if not isinstance(current_price, (int, float, Decimal)) or current_price <= 0:
        raise ValueError("O valor do current_price deve ser um número positivo.")

      step_size = None
      min_quantity = None
      min_notional = None

      for filter in symbol_info['filters']:
        if filter['filterType'] == 'LOT_SIZE':
            step_size = Decimal(filter['stepSize'])
            min_quantity = Decimal(filter['minQty'])
        if filter['filterType'] == 'NOTIONAL':
            min_notional = Decimal(filter['minNotional'])

      if step_size is None or min_quantity is None or min_notional is None:
        raise ValueError("Não foi possível encontrar 'stepSize', 'minQty' ou 'minNotional'.")

      # Calcula a quantidade mínima para o notional:
      min_quantity_notional = (Decimal(min_notional) / Decimal(current_price)).quantize(step_size, rounding=ROUND_UP)

      # Calcula a quantidade máxima teórica (sem restrições):
      max_quantity_temp = Decimal(available_balance) / Decimal(current_price)

      # Ajusta a quantidade máxima para baixo, respeitando o step_size:
      max_quantity = max_quantity_temp.quantize(step_size, rounding=ROUND_DOWN)

      # **Correção crucial:** Garante que max_quantity atende ao min_notional, ajustando em incrementos de step_size se necessário:
      while max_quantity * Decimal(current_price) < Decimal(min_notional):
        max_quantity += step_size

      # Garante que max_quantity respeita min_quantity
      max_quantity = max(max_quantity, min_quantity)


      erro_logger.info(f"Saldo Disponível: {available_balance}, Preço Atual: {current_price}, "
                         f"step_size: {step_size}, min_quantity: {min_quantity}, min_notional: {min_notional}, "
                         f"Quantidade Máxima de Venda Calculada: {max_quantity}")

      return max_quantity






