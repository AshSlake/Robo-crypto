from binance.exceptions import BinanceAPIException, BinanceRequestException
from functions.logger import erro_logger


def getActualTradePositionForBinance(self):
    try:
        trades = self.client_binance.get_my_trades(symbol=self.operation_code, limit=1)
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
