import os
import time
from typing import Self
import pandas as pd
from datetime import datetime
from flask import Flask, send_file
import threading
from dotenv import load_dotenv
from binance.client import Client
from binance.enums import *
from binance.exceptions import BinanceAPIException, BinanceRequestException
import estrategias.TradingStrategies as TradingStrategies
from functions.logger import createLogOrder, erro_logger, trade_logger, bot_logger
from decimal import ROUND_DOWN, Decimal
from functions.calculate_max_buy_sell_quantity import QuantityCalculator


# Load environment variables
load_dotenv()

api_key = os.getenv("BINANCE_API_KEY")
secret_key = os.getenv("BINANCE_SECRET_KEY")

# Configurations
STOCK_CODE = "SOL"
OPERATION_CODE = "SOLUSDT"
CANDLE_PERIOD = Client.KLINE_INTERVAL_15MINUTE
TRADED_QUANTITY = 0.56

# Flask app for serving logs
app = Flask(__name__)


@app.route("/logs")
def get_logs():
    log_file_path = "C:/Users/paulo/python/Robo crypto/logs/trades.log"
    if os.path.exists(log_file_path):
        return send_file(log_file_path, as_attachment=True)
    else:
        return f"Arquivo de log não encontrado no caminho: {log_file_path}", 404


def run_server():
    app.run(host="0.0.0.0", port=5000)


server_thread = threading.Thread(target=run_server)
server_thread.start()


# Binance Trading Bot Class
class BinanceTraderBot:
    last_trade_decision: bool = False
    last_profit = None

    def __init__(
        self,
        stock_code,
        operation_code,
        traded_quantity,
        traded_percentage,
        candle_period,
    ):
        self.stock_code = stock_code
        self.operation_code = operation_code
        self.traded_quantity = traded_quantity
        self.traded_percentage = traded_percentage
        self.candle_period = candle_period
        self.client_binance = Client(api_key, secret_key)
        self.quantity_calculator = QuantityCalculator(
            self.client_binance, self.operation_code
        )  # Instancia a classe
        print("Robo Trader iniciado...")
        bot_logger.info("Robo Trader iniciado...")

    def updateAllData(self):
        try:
            self.account_data = self.getUpdatedAccountData()
            self.last_stock_account_balance = self.getLastStockAccountBalance()
            self.actual_trade_position = self.getActualTradePositionForBinance()
            self.stock_data = self.getStockData()
        except Exception as e:
            erro_logger.exception(
                f"------------------------------------\nErro ao atualizar dados: {e}"
            )
            erro_logger.exception(f"------------------------------------\n")

    def getUpdatedAccountData(self):
        return self.client_binance.get_account()

    def getLastStockAccountBalance(self):
        for stock in self.account_data["balances"]:
            if stock["asset"] == self.stock_code:
                return float(stock["free"])
        return 0.0

    def getActualTradePositionForBinance(self):
        try:
            trades = self.client_binance.get_my_trades(
                symbol=self.operation_code, limit=1
            )
            if trades:
                last_trade = trades[0]
                return last_trade[
                    "isBuyer"
                ]  # True se a última ordem foi compra, False se foi venda
            else:
                # Se não houver negociações, assume que a posição é vendida (ou neutra)
                return False
        except BinanceAPIException as e:
            erro_logger.exception(
                f"Erro na Binance API ao obter a posição de negociação: {e}"
            )
            return False  # Retorna False em caso de erro para evitar compras acidentais
        except Exception as e:
            erro_logger.exception(f"Erro ao obter a posição de negociação: {e}")
            return False

    # Prints

    def printAllWallet(self):
        # Printa toda a carteira
        for stock in self.account_data["balances"]:
            if float(stock["free"]) > 0:
                print(stock)

    def printStock(self):
        # Printa o ativo definido na classe
        for stock in self.account_data["balances"]:
            if stock["asset"] == self.stock_code:
                print(stock)

    def printBrl(self):
        for stock in self.account_data["balances"]:
            if stock["asset"] == "BRL":
                print(stock)

    def getStockData(self):
        candles = self.client_binance.get_klines(
            symbol=self.operation_code, interval=self.candle_period, limit=500
        )
        prices = pd.DataFrame(
            candles,
            columns=[
                "open_time",
                "open_price",
                "high_price",
                "low_price",
                "close_price",
                "volume",
                "close_time",
                "quote_asset_volume",
                "number_of_trades",
                "taker_buy_base_asset_volume",
                "taker_buy_quote_asset_volume",
                "ignore",
            ],
        )
        prices = prices[["close_price", "open_time"]]
        prices["open_time"] = (
            pd.to_datetime(prices["open_time"], unit="ms")
            .dt.tz_localize("UTC")
            .dt.tz_convert("America/Sao_Paulo")
        )
        return prices

    def calculate_profit(self, entry_price, quantity, current_price):
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
        profit_per_unit = current_price - entry_price
        total_profit = profit_per_unit * quantity
        return total_profit

    def log_profit(self, entry_price, quantity, current_price):
        profit = self.calculate_profit(entry_price, quantity, current_price)
        if profit is not None:
            symbol = "+" if profit >= 0 else "-"
            bot_logger.info(
                f"Lucro/Prejuízo da operação: {symbol}{abs(profit):.8f} USDT"
            )

    def execute_trade(self, side):
        quantity = None  # Inicializa quantity como None
        try:
            # Obtenha informações do símbolo para obter stepSize e minQty (quantidade mínima)
            current_price = Decimal(
                self.client_binance.get_symbol_ticker(symbol=self.operation_code)[
                    "price"
                ]
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

            if order and order["status"] in ("FILLED", "PARTIALLY_FILLED"):
                log_message = (
                    createLogOrder(order) if createLogOrder else "No log message"
                )
                bot_logger.info(log_message)
                trade_logger.info(log_message)

            if order["status"] == "FILLED":
                log_message = (
                    createLogOrder(order) if createLogOrder else "No log message"
                )
                bot_logger.info(log_message)
                trade_logger.info(log_message)
                self.actual_trade_position = True if side == SIDE_BUY else False
                self.updateAllData()

            elif order["status"] == "PARTIALLY_FILLED":
                bot_logger.warning(
                    f"Ordem {side} parcialmente preenchida. Verifique o status da ordem."
                )
                self.actual_trade_position = True if side == SIDE_BUY else False
                self.traded_quantity = float(order["executedQty"])
                if self.actual_trade_position == True:
                    self.entry_price = Decimal(order["fills"][0]["price"])
                    self.purchased_quantity = Decimal(order["executedQty"])
                else:
                    current_price = Decimal(
                        self.client_binance.get_symbol_ticker(
                            symbol=self.operation_code
                        )["price"]
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

    def get_balance(self):
        account_info = self.client_binance.get_account()
        for asset in account_info["balances"]:
            if asset["asset"] == "USDT":
                return float(asset["free"])
        return 0.0

    def message_bot_logger_info(self, message):
        bot_logger.info(message)

    def execute(self):
        try:
            self.updateAllData()
            # Obtém dados do símbolo
            print(f"\n-----------------------------")
            print(
                f'Executado: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'
            )  # Adiciona o horário atual
            print(
                f'Posição atual: {"Comprado" if MaTrader.actual_trade_position else "Vendido" }'
            )
            print(
                f"Balanço atual: {MaTrader.last_stock_account_balance} ({self.stock_code})"
            )
            if self.last_profit is not None:  # Exibe apenas se houver lucro registrado.
                print(f"Lucro da última venda: {self.last_profit:.8f} USDT")
            print(f"-----------------------------\n")

            message = (
                f"-----------------------------\n"
                f'Executado: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n'
                f'Posição atual: {"Comprado" if self.actual_trade_position else "Vendido"}\n'
                f"Balanço atual: {self.last_stock_account_balance} ({self.stock_code})\n"
                f"-----------------------------\n"
            )
            if self.last_profit is not None:
                message += f"Lucro da última venda: {self.last_profit:.8f} USDT\n"
            message += f"-----------------------------\n"
            bot_logger.info(message)

            # Usa getActualTradePositionForBinance para obter a posição atual do trade
            self.actual_trade_position = self.getActualTradePositionForBinance()

            # Cria uma instância da classe `estrategies`
            estrategias = TradingStrategies.estrategies(
                stock_data=self.stock_data,
                operation_code=self.stock_code,  # Passa o código da operação
                actual_trade_position=self.actual_trade_position,
            )

            ma_trade_decision = estrategias.getMovingAverageVergenceRSI(
                fast_window=7, slow_window=40, volatility_factor=0.3
            )

            if ma_trade_decision and not self.actual_trade_position:
                self.execute_trade(SIDE_BUY)
                self.actual_trade_position = (
                    self.getActualTradePositionForBinance()
                )  # ou True, se tiver certeza da compra
            elif not ma_trade_decision and self.actual_trade_position:
                self.execute_trade(SIDE_SELL)
                self.actual_trade_position = (
                    self.getActualTradePositionForBinance()
                )  # ou False, se tiver certeza da venda

        except BinanceRequestException as e:  # Captura erros de requisição da Binance
            erro_logger.error(f"Erro de requisição da Binance: {e}")
            bot_logger.warning("Tentando reconectar à Binance em 60 segundos...")
            time.sleep(60)  # Aguarda 60 segundos antes de tentar novamente


# Main execution loop
MaTrader = BinanceTraderBot(
    STOCK_CODE, OPERATION_CODE, TRADED_QUANTITY, 100, CANDLE_PERIOD
)
while True:
    MaTrader.execute()
    time.sleep(60)
