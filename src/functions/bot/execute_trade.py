from decimal import Decimal
from binance.exceptions import BinanceAPIException, BinanceRequestException
from functions.logger import createLogOrder, erro_logger, trade_logger, bot_logger
from functions.logger import createLogOrder


def execute_trade(
    self, side, SIDE_BUY, ORDER_TYPE_MARKET, SIDE_SELL, ROUND_DOWN, OPERATION_CODE
):
    quantity = None  # Inicializa quantity como None
    try:
        # Obtenha informações do símbolo para obter stepSize e minQty (quantidade mínima)
        current_price = Decimal(
            self.client_binance.get_symbol_ticker(symbol=self.operation_code)["price"]
        )
        symbol_info = self.client_binance.get_symbol_info(self.operation_code)

        step_size = min_quantity = min_notional = None

        # Processa os filtros necessários
        step_size = min_quantity = min_notional = 0
        for filter in symbol_info["filters"]:
            if filter["filterType"] == "LOT_SIZE":
                step_size = Decimal(filter["stepSize"])
                min_quantity = Decimal(filter["minQty"])
            elif filter["filterType"] == "NOTIONAL":
                min_notional = Decimal(filter["minNotional"])

        # Validação
        if step_size == 0 or min_quantity == 0 or min_notional == 0:
            raise ValueError(
                "Não foi possível obter 'stepSize', 'minQty' ou 'minNotional'"
            )

        # Verificando se os filtros estão presentes
        if "filters" not in symbol_info:
            raise ValueError(
                f"Os filtros não estão presentes para o símbolo {self.operation_code}. Verifique o par de moedas."
            )
        # Logar os filtros disponíveis para depuração
        # for filter in symbol_info['filters']:
        # print(filter)  # Isso ajudará a ver quais filtros estão disponíveis

        if side == SIDE_BUY:
            balance = self.get_balance()

            quantity = self.quantity_calculator.calculate_max_buy_quantity(
                symbol_info, balance, current_price
            )

            # Arredonda para baixo para o step_size mais próximo
            quantity = (quantity // step_size) * step_size

            # Garante que a quantidade seja maior ou igual ao mínimo
            quantity = max(quantity, min_quantity)

            if quantity < min_quantity:
                raise ValueError(
                    f"Quantidade de compra menor que o mínimo permitido: {min_quantity}"
                )
            order = self.client_binance.create_order(
                symbol=self.operation_code,
                side=SIDE_BUY,
                type=ORDER_TYPE_MARKET,
                quantity=str(quantity),
            )

        elif side == SIDE_SELL:
            # Obtem o saldo disponível do ativo
            available_balance = Decimal(self.getLastStockAccountBalance())

            # Arredonda available_balance para baixo de acordo com step_size
            quantity = (available_balance / step_size).quantize(
                1, rounding=ROUND_DOWN
            ) * step_size

            # Verifica se atende ao requisito mínimo
            if quantity * current_price < min_notional:
                erro_logger.error(
                    f"Valor da venda abaixo do mínimo permitido ({min_notional:.8f}). Saldo disponível: {available_balance}, current_price: {current_price} quantity: {quantity}"
                )
                erro_logger.error(f"iniciando correção do valor da venda")

                quantity = self.quantity_calculator.calculate_max_sell_quantity(
                    symbol_info, available_balance, current_price
                )

                # Arredonda para baixo para o step_size mais próximo
                quantity = (quantity // step_size) * step_size

                # Garante que a quantidade seja maior ou igual ao mínimo
                quantity = max(quantity, min_quantity)
                trade_logger.info(
                    f"Corrigindo ordem de VENDA: {self.operation_code}, Quantidade: {quantity}, Preço: {current_price}"
                )
            order = self.client_binance.create_order(
                symbol=self.operation_code,
                side=SIDE_SELL,
                type=ORDER_TYPE_MARKET,
                quantity=str(quantity),
            )

        if order["status"] == "FILLED":
            (
                createLogOrder(order, OPERATION_CODE)
                if createLogOrder
                else "No log message"
            )
            self.actual_trade_position = True if side == SIDE_BUY else False
            self.traded_quantity = float(order["executedQty"])
            if self.actual_trade_position == True:
                self.entry_price = Decimal(order["fills"][0]["price"])
                self.purchased_quantity = Decimal(order["executedQty"])
            else:
                current_price = Decimal(
                    self.client_binance.get_symbol_ticker(symbol=self.operation_code)[
                        "price"
                    ]
                )
            profit = self.calculate_profit(
                self.entry_price, self.purchased_quantity, current_price
            )
            self.last_profit = profit  # Armazena o lucro
            self.entry_price = None  # Reseta o entry_price
            self.purchased_quantity = None
            self.updateAllData()

        elif order["status"] == "PARTIALLY_FILLED":
            trade_logger.info(
                f"Ordem {side} parcialmente preenchida. Verifique o status da ordem."
            )
            self.actual_trade_position = True if side == SIDE_BUY else False
            self.traded_quantity = float(order["executedQty"])
            if self.actual_trade_position == True:
                self.entry_price = Decimal(order["fills"][0]["price"])
                self.purchased_quantity = Decimal(order["executedQty"])
            else:
                current_price = Decimal(
                    self.client_binance.get_symbol_ticker(symbol=self.operation_code)[
                        "price"
                    ]
                )
            profit = self.calculate_profit(
                self.entry_price, self.purchased_quantity, current_price
            )
            self.last_profit = profit  # Armazena o lucro
            self.entry_price = None  # Reseta o entry_price
            self.purchased_quantity = None
            self.updateAllData()

        return order

    except BinanceAPIException as e:
        erro_logger.exception(
            f"Erro da Binance API ({side}): {e}, quantity: {quantity}"
        )
    except ValueError as e:
        erro_logger.exception(
            f"Erro de validação de quantidade ({side}): {e}, quantity: {quantity if quantity is not None else 'N/A'}"
        )
    except Exception as e:
        erro_logger.exception(
            f"Outro erro em execute_trade ({side}): {e}, quantity: {quantity if quantity is not None else 'N/A'}"
        )
        return None
