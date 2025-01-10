import os
import trace
from dotenv import load_dotenv
from datetime import datetime
import time
import estrategias.TradingStrategies as TradingStrategies
from logger import *
from binance.exceptions import BinanceAPIException
from binance.client import Client
from binance.enums import *
import pandas as pd
import logging
from flask import Flask, send_file
import threading


api_key = os.getenv('BINANCE_API_KEY')
secret_key = os.getenv('BINANCE_SECRET_KEY')


# CONFIGURAÇÕES

STOCK_CODE = "SOL"
OPERATION_CODE = "SOLUSDT" # Cliente.KLINE_INTERVAL_1MINUTE
CANDLE_PERIOD = Client.KLINE_INTERVAL_15MINUTE
TRADED_QUANTITY = 0.03


# Criação da instância Flask
app = Flask(__name__)

# Função para servir o arquivo de log
@app.route('/logs')
def get_logs():
    log_file_path = 'C:/Users/paulo/python/Robo crypto/src/logs/trading_bot.log'  # Caminho do arquivo de log
    if os.path.exists(log_file_path):
        return send_file(log_file_path, as_attachment=True)
    else:
        return f"Arquivo de log não encontrado no caminho: {log_file_path}", 404

# Função para rodar o servidor Flask
def run_server():
    app.run(host='0.0.0.0', port=5000)

# Cria e inicia a thread para o servidor
server_thread = threading.Thread(target=run_server)
server_thread.start()

# Classe Principal
class BinanceTraderBot():


    last_trade_decision: bool = False # Última decisão de posição (False = Vender | True = Comprar)

    def __init__(self, stock_code, operation_code, traded_quantity, traded_percentage, candle_period):

        self.stock_code = stock_code # Código principal da stock negociada (ex.: 'BTC')
        self.operation_code = operation_code # Código negociado/moeda (ex.: 'BTCBRL')
        self.traded_quantity = traded_quantity # Quantidade inicial que será operada
        self.traded_percentage = traded_percentage # Porcentagem do total da carteira, que será negociada
        self.candle_period = candle_period # Período levado em consideração para operação (ex: 15min)
        self.volatility_factor = 2.0
        self.client_binance = Client(api_key, secret_key) # Inicia o cliente da Binance

        self.updateAllData()

        print('Robo Trader iniciado...')

    # Atualiza todos os dados da conta
    def updateAllData(self):
        self.account_data = self.getUpdatedAccountData() # Dados atualizados do usuário e sua carteira
        self.last_stock_account_balance = self.getLastStockAccountBalance() # Balanço atual do ativo na carteira
        self.actual_trade_position = self.getActualTradePosition() # Posição atual (False = Vendido | True = Comprado)
        self.stock_data = self.getStockData() # Atualiza dados usados nos modelos

    # Busca infos atualizada da conta Binance
    def getUpdatedAccountData(self):
        return self.client_binance.get_account()

    # Busca o último balanço da conta, na stock escolhida.
    def getLastStockAccountBalance(self):

        for stock in self.account_data['balances']:
            if stock['asset'] == self.stock_code:
                in_wallet_amount = stock['free']

        return float(in_wallet_amount)

    # Checa se a posição atual é comprada ou vendida
    def getActualTradePosition(self):
        # Futuramente integrar com banco de dados para
        # Guardar este dado com mais precisão.

        if self.getLastStockAccountBalance() > 0.001:
            return True # Comprado
        else:
            return False # Está vendido

    # Busca os dados do ativo no período
    def getStockData(self):
        candles = self.client_binance.get_klines(symbol = self.operation_code, interval = self.candle_period, limit = 500)
        
        prices = pd.DataFrame(candles)
        prices.columns = ['open_time', 'open_price', 'high_price', 'low_price', 'close_price', 
                     'volume', 'close_Time', 'quote_asset_volume', 'number_of_trades',
                     'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', '-']

        prices = prices[['close_price', 'open_time']]

        # Corrige o tempo de fechamento
        prices['open_time'] = pd.to_datetime(prices['open_time'], unit = 'ms').dt.tz_localize('UTC')

        # Converte para o fuso horário UTC - 3
        prices['open_time'] = prices['open_time'].dt.tz_convert('America/Sao_Paulo')

        return prices

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


    # GETS auxiliares

    def getAllWallet(self):
        # Retorna toda a carteira
        for stock in self.account_data['balances']:
            if float(stock['free']) > 0:
                return stock

    def getStock(self):
        # Retorna todo o ativo definido na classe
        for stock in self.account_data['balances']:
            if stock['asset'] == self.stock_code:
                return stock


    def buyStock(self):
      try:
        # Obtenha informações do símbolo para obter stepSize e minQty (quantidade mínima)
        symbol_info = self.client_binance.get_symbol_info(self.operation_code)
        
        step_size = min_quantity = 0
        for filter in symbol_info['filters']:
            if filter['filterType'] == 'LOT_SIZE':
                step_size = float(filter['stepSize'])
                min_quantity = float(filter['minQty'])
                break
        
        if step_size == 0 or min_quantity == 0:
            raise ValueError("Não foi possível obter 'stepSize' ou 'minQty'")
        
        # Ajuste a quantidade a ser comprada para garantir que seja um múltiplo de stepSize e maior ou igual a minQty
        quantity_to_buy = max(min_quantity, round(self.traded_quantity / step_size) * step_size)

        if self.actual_trade_position == False:  # Se a posição for vendida
            order_buy = self.client_binance.create_order(
                symbol=self.operation_code,
                side=SIDE_BUY,
                type=ORDER_TYPE_MARKET,
                quantity=quantity_to_buy,
            )
            self.actual_trade_position = True  # Define posição como comprada

            createLogOrder(order_buy)  # Cria um log
            return order_buy  # Retorna a ordem

        else:  # Se já está comprado ou ocorre algum outro erro
            logging.warning('Erro: Posição já comprada ou erro ao comprar')
            print('Erro ao comprar')
            return False

      except BinanceAPIException as e:
        logging.error(f"Erro ao comprar: {e}")
        return False
      except ValueError as ve:
        logging.error(f"Erro nos dados do símbolo: {ve}")
        return False


    def sellStock(self):
      try:
        # Obtenha informações do símbolo para obter stepSize e minQty (quantidade mínima)
        symbol_info = self.client_binance.get_symbol_info(self.operation_code)
        
        step_size = min_quantity = 0
        for filter in symbol_info['filters']:
            if filter['filterType'] == 'LOT_SIZE':
                step_size = float(filter['stepSize'])
                min_quantity = float(filter['minQty'])
                break
        
        if step_size == 0 or min_quantity == 0:
            raise ValueError("Não foi possível obter 'stepSize' ou 'minQty'")

        # Verifique o saldo disponível e ajuste a quantidade a ser vendida
        available_balance = float(self.getStock()['free'])
        quantity_to_sell = min(available_balance, self.traded_quantity)  # Não vende mais que o que possui

        # Se a quantidade desejada de venda for inferior à quantidade mínima, não permita a venda
        if quantity_to_sell < min_quantity:
            logging.warning(f"Saldo insuficiente para vender. Quantidade mínima: {min_quantity}, quantidade disponível: {quantity_to_sell}")
            return False

        # Garanta que a quantidade seja um múltiplo de stepSize
        quantity_to_sell = max(min_quantity, round(quantity_to_sell / step_size) * step_size)

        # Verifique se a quantidade a ser vendida não excede o saldo disponível
        if quantity_to_sell > available_balance:
            logging.warning(f"Tentativa de vender mais do que o saldo disponível. Quantidade ajustada: {available_balance}")
            quantity_to_sell = available_balance

        # Verifique se a quantidade é válida
        if quantity_to_sell < min_quantity:
            logging.warning(f"Quantidade ajustada para venda é menor que o mínimo permitido. Não vendendo.")
            return False

        # Realize a venda
        order_sell = self.client_binance.create_order(
            symbol=self.operation_code,
            side=SIDE_SELL,
            type=ORDER_TYPE_MARKET,
            quantity=quantity_to_sell,
        )
        self.actual_trade_position = False  # Define posição como vendida

        createLogOrder(order_sell)  # Cria um log
        return order_sell  # Retorna a ordem

      except BinanceAPIException as e:
        logging.error(f"Erro ao vender: {e}")
        return False
      except ValueError as ve:
        logging.error(f"Erro nos dados do símbolo: {ve}")
        return False


    def execute(self):
        # Atualiza todos os dados

        self.updateAllData()

        print(f'Executado: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}') # Adiciona o horário atual
        print(f'Posição atual: {"Comprado" if MaTrader.actual_trade_position else "Vendido" }')
        print(f'Balanço atual: {MaTrader.last_stock_account_balance} ({self.stock_code})')


        # Executa a estratégia de média móvel
        ma_trade_decision = TradingStrategies.estrategies.getMovingAverageTradeStrategy(self,fast_window=7, slow_window=40)

        # Neste caso, a decisão final será a mesma da média móvel.
        self.last_trade_decision = ma_trade_decision

        # Se a posição for vendida (false) e a decisao for de compra (true), compra o ativo
        # Se a posição for comprada (true) e a decisao for de venda (false), vende o ativo
        if self.actual_trade_position == False and self.last_trade_decision == True:

            self.printStock()
            self.buyStock()
            self.printStock()

            time.sleep(2)
            self.updateAllData()

            self.printStock()
            self.printBrl()
            time.sleep(2)



        elif self.actual_trade_position == True and self.last_trade_decision == False:

            self.printStock()
            self.sellStock()
            self.printStock()
            time.sleep(2)

            self.updateAllData()

            self.printStock()
            self.printBrl()
            time.sleep(2)
            


        print('----------------')

        # LOOP PRINCIPAL
MaTrader = BinanceTraderBot(STOCK_CODE, OPERATION_CODE, TRADED_QUANTITY, 100, CANDLE_PERIOD)


while(1):
 MaTrader.execute()
 time.sleep(60)
