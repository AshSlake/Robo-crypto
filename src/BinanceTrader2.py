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
from binance.exceptions import BinanceAPIException
import estrategias.TradingStrategies as TradingStrategies
from logger import createLogOrder, erro_logger, trade_logger, bot_logger

# Load environment variables
load_dotenv()

api_key = os.getenv('BINANCE_API_KEY')
secret_key = os.getenv('BINANCE_SECRET_KEY')

# Configurations
STOCK_CODE = "SOL"
OPERATION_CODE = "SOLUSDT"
CANDLE_PERIOD = Client.KLINE_INTERVAL_15MINUTE
TRADED_QUANTITY = 0.03

# Flask app for serving logs
app = Flask(__name__)

@app.route('/logs')
def get_logs():
    log_file_path = 'C:/Users/paulo/python/Robo crypto/src/logs/trading_bot.log'
    if os.path.exists(log_file_path):
        return send_file(log_file_path, as_attachment=True)
    else:
        return f"Arquivo de log não encontrado no caminho: {log_file_path}", 404

def run_server():
    app.run(host='0.0.0.0', port=5000)

server_thread = threading.Thread(target=run_server)
server_thread.start()      

# Binance Trading Bot Class
class BinanceTraderBot:
    last_trade_decision: bool = False

    def __init__(self, stock_code, operation_code, traded_quantity, traded_percentage, candle_period):
        self.stock_code = stock_code
        self.operation_code = operation_code
        self.traded_quantity = traded_quantity
        self.traded_percentage = traded_percentage
        self.candle_period = candle_period
        self.client_binance = Client(api_key, secret_key)
        self.updateAllData()
        print('Robo Trader iniciado...')
        bot_logger.info("Robo Trader iniciado...")

    def updateAllData(self):
        try:
            self.account_data = self.getUpdatedAccountData()
            self.last_stock_account_balance = self.getLastStockAccountBalance()
            self.actual_trade_position = self.getActualTradePosition()
            self.stock_data = self.getStockData()
        except Exception as e:
            erro_logger.exception(f"Erro ao atualizar dados: {e}")

    def getUpdatedAccountData(self):
        return self.client_binance.get_account()

    def getLastStockAccountBalance(self):
        for stock in self.account_data['balances']:
            if stock['asset'] == self.stock_code:
                return float(stock['free'])
        return 0.0

    # Checa se a posição atual é comprada ou vendida
    def getActualTradePosition(self):
        # Futuramente integrar com banco de dados para
        # Guardar este dado com mais precisão.

        if self.getLastStockAccountBalance() > 0.001:
            return True # Comprado
        else:
            return False # Está vendido
        
    # Prints

    def printAllWallet(self):
        # Printa toda a carteira
        for stock in self.account_data['balances']:
            if float(stock['free']) > 0:
                print(stock)
    
    def printStock(self):
        # Printa o ativo definido na classe
        for stock in self.account_data['balances']:
            if stock['asset'] == self.stock_code:
                print(stock)

    def printBrl(self):
        for stock in self.account_data['balances']:
            if stock['asset'] == "BRL":
                print(stock)

    def getStockData(self):
        candles = self.client_binance.get_klines(symbol=self.operation_code, interval=self.candle_period, limit=500)
        prices = pd.DataFrame(candles, columns=['open_time', 'open_price', 'high_price', 'low_price', 'close_price',
                                                'volume', 'close_time', 'quote_asset_volume', 'number_of_trades',
                                                'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'])
        prices = prices[['close_price', 'open_time']]
        prices['open_time'] = pd.to_datetime(prices['open_time'], unit='ms').dt.tz_localize('UTC').dt.tz_convert('America/Sao_Paulo')
        return prices

    def execute_trade(self, side):
        try:
            symbol_info = self.client_binance.get_symbol_info(self.operation_code)

            step_size = min_quantity = 0
            for filter in symbol_info['filters']:
                if filter['filterType'] == 'LOT_SIZE':
                    step_size = float(filter['stepSize'])
                    min_quantity = float(filter['minQty'])
                    break
            if step_size == 0 or min_quantity == 0:
                raise ValueError("Invalid step size or min quantity.")
            quantity = max(min_quantity, round(self.traded_quantity / step_size) * step_size)

            if side == SIDE_BUY and not self.actual_trade_position:
                order = self.client_binance.create_order(symbol=self.operation_code, side=SIDE_BUY, type=ORDER_TYPE_MARKET, quantity=quantity)
                self.actual_trade_position = True

                log_message = createLogOrder(order)
                trade_logger.info(f"Compra realizada com sucesso. Detalhes da ordem: {log_message}")

            elif side == SIDE_SELL and self.actual_trade_position:
                available_balance = self.getLastStockAccountBalance()
                quantity = min(available_balance, quantity)
                if quantity < min_quantity:
                    raise ValueError("Insufficient balance to sell.")
                order = self.client_binance.create_order(symbol=self.operation_code, side=SIDE_SELL, type=ORDER_TYPE_MARKET, quantity=quantity)
                self.actual_trade_position = False

                log_message = createLogOrder(order) # Guarda a mensagem retornada de createLogOrder
                trade_logger.info(f"Venda realizada com sucesso. Detalhes da ordem: {log_message}")
            return order
        except Exception as e:
            erro_logger.exception(f"Erro na execução do bot: {e}")  # Loga a exceção completa com traceback
        return None
    
    def message_bot_logger_info(self, message):
     bot_logger.info(message)
        

    def execute(self):
        try:
            self.updateAllData()
            ma_trade_decision = TradingStrategies.estrategies.getMovingAverageVergenceTradeStrategy(self,fast_window=7,slow_window=40,volatility_factor=2)

            print(f'Executado: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}') # Adiciona o horário atual
            print(f'Posição atual: {"Comprado" if MaTrader.actual_trade_position else "Vendido" }')
            print(f'Balanço atual: {MaTrader.last_stock_account_balance} ({self.stock_code})')

            message = (
              f'{'----------------------------'}\n'
              f'Executado: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n'
              f'Posição atual: {"Comprado" if self.actual_trade_position else "Vendido"}\n'
              f'Balanço atual: {self.last_stock_account_balance} ({self.stock_code})\n'
              f'{'----------------------------'}\n'
            )
            self.message_bot_logger_info(message)
             

            if not self.actual_trade_position:
                if ma_trade_decision:
                    order = self.execute_trade(SIDE_BUY)
                    if order:
                        self.actual_trade_position = True
                        self.printStock()
                        self.printBrl()
                        self.updateAllData

            elif self.actual_trade_position:
                if not ma_trade_decision:
                    order = self.execute_trade(SIDE_SELL)
                    if order:
                        self.actual_trade_position = False
                        self.printStock()
                        self.printBrl()
                        self.updateAllData
                else:
                    bot_logger.info("No action")

        except Exception as e:
            erro_logger.exception(f"Erro na execução do bot: {e}") 

# Main execution loop
MaTrader = BinanceTraderBot(STOCK_CODE, OPERATION_CODE, TRADED_QUANTITY, 100, CANDLE_PERIOD)
while True:
    MaTrader.execute()
    time.sleep(60)
