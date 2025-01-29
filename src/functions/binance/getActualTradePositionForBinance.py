from binance.exceptions import BinanceAPIException
from binance.client import Client as client_binance
from functions.logger import erro_logger


def __init__(self):
    self.client_binance = client_binance()


def getActualTradePositionForBinance(self, operation_code):
    try:
        trades = client_binance.get_my_trades(
            self.client_binance, symbol=operation_code, limit=1
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
