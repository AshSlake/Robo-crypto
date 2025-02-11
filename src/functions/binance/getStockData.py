import os
import pandas as pd
from binance.client import Client as client_binance

api_key = os.getenv("BINANCE_API_KEY")
secret_key = os.getenv("BINANCE_SECRET_KEY")
client_binance = client_binance(api_key, secret_key)


class StockDataCollector:
    def __init__(self, operation_code, candle_period, limit=500):
        self.operation_code = operation_code
        self.candle_period = candle_period
        self.limit = limit

    def getStockData(self):
        try:
            candles = client_binance.get_klines(
                symbol=self.operation_code,
                interval=self.candle_period,
                limit=self.limit,
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
            prices["open_time"] = (
                pd.to_datetime(prices["open_time"], unit="ms")
                .dt.tz_localize("UTC")
                .dt.tz_convert("America/Sao_Paulo")
            )
            return prices
        except Exception as e:
            print(f"Error getting stock data: {e}")
            return None
