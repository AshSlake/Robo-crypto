import os
from symtable import Symbol
from binance.exceptions import BinanceAPIException
from functions.logger import erro_logger
from binance.client import Client


class BinancePositionManager:
    # Método para recuperar a posição de negociação do ativo em Binance
    def __init__(self, symbol, limit=1):
        self.client_binance = Client(
            os.getenv("BINANCE_API_KEY"),
            os.getenv("BINANCE_SECRET_KEY"),
        )
        self.symbol = symbol
        self.limit = limit

    def getActualTradePositionForBinance(self):
        try:
            trades = self.client_binance.get_my_trades(
                symbol=self.symbol, limit=self.limit
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
