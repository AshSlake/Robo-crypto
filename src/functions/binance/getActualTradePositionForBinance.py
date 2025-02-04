import os
from symtable import Symbol
from binance.exceptions import BinanceAPIException
from functions.logger import erro_logger
from binance.client import Client


def getActualTradePositionForBinance(symbol, limit):
    api_key = os.getenv("BINANCE_API_KEY")
    secret_key = os.getenv("BINANCE_SECRET_KEY")
    client_binance = Client(api_key, secret_key)
    try:
        trades = client_binance.get_my_trades(symbol=symbol, limit=limit)
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
