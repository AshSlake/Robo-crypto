from functions.binance.getActualTradePositionForBinance import BinancePositionManager
from functions.binance.getStockData import StockDataCollector
from functions.binance.smallGetsFromBinance import AdministratorFromSmallGets
from binance.client import Client
from functions.logger import erro_logger
import os
import dotenv
import traceback

# Load environment variables
dotenv.load_dotenv()

api_key = os.getenv("BINANCE_API_KEY")
secret_key = os.getenv("BINANCE_SECRET_KEY")


class UpdateAllData:
    def __init__(self, stock_code, operation_code, candle_period):
        try:
            self.client_binance = Client(api_key, secret_key)
            self.getAccount_data = self.getUpdatedAccountData()
            afg = AdministratorFromSmallGets(
                account_data=self.getAccount_data,
                stock_code=stock_code,
            )
            trade_position = BinancePositionManager(symbol=operation_code, limit=1)
            self.getUpdatedAccountData = self.getUpdatedAccountData()
            self.getLastStockAccountBalance = afg.getLastStockAccountBalance()
            self.getActualTradePositionForBinance = (
                trade_position.getActualTradePositionForBinance()
            )
            self.getStockData = StockDataCollector(
                operation_code=operation_code, candle_period=candle_period
            )
        except Exception as e:
            traceback_info = traceback.format_exc()
            erro_logger.exception(
                f"erro no __init__,localização do erro:\n{traceback_info}"
            )
            print(f"erro no __init__,localização do erro:\n{traceback_info}")

    def updateAllData(self):
        try:
            account_data = self.getAccount_data
            last_stock_account_balance = self.getLastStockAccountBalance
            actual_trade_position = self.getActualTradePositionForBinance
            df = self.getStockData.getStockData()

            results = {
                "account_data": account_data,
                "last_stock_account_balance": last_stock_account_balance,
                "actual_trade_position": actual_trade_position,
                "stock_data": df,
            }
            return results
        except Exception as e:
            traceback_info = traceback.format_exc()
            erro_logger.exception(
                f"Erro no updateAllData, localização do erro:\n{traceback_info}"
            )
            print(f"Erro no updateAllData, localização do erro:\n{traceback_info}")

    def getUpdatedAccountData(self):
        try:
            return self.client_binance.get_account()
        except Exception as e:
            traceback_info = traceback.format_exc()
            erro_logger.exception(
                f"Erro no getUpdatedAccountData, localização do erro:\n{traceback_info}"
            )
            print(
                f"Erro no getUpdatedAccountData, localização do erro:\n{traceback_info}"
            )
