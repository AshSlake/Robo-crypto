import os
from dotenv import load_dotenv
from datetime import datetime
import time
from logger import *
from binance.client import Client
from binance.enums import *
import pandas as pd


api_key = os.getenv('BINANCE_API_KEY')
secret_key = os.getenv('BINANCE_SECRET_KEY')


# CONFIGURAÇÕES

STOCK_CODE = "DOGE"
OPERATION_CODE = "DOGEBRL" # Cliente.KLINE_INTERVAL_1MINUTE
CANDLE_PERIOD = Client.KLINE_INTERVAL_15MINUTE
TRADED_QUANTITY = 16


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

    # Executa a estratégia de média móvel
    def getMovingAverageTradeStrategy(self, fast_window = 7, slow_window = 40):

        # Calcula as Médias Móveis Rápida e Lenta
        self.stock_data['ma_fast'] = self.stock_data['close_price'].rolling(window=fast_window).mean() # Média Rápida
        self.stock_data['ma_slow'] = self.stock_data['close_price'].rolling(window=slow_window).mean() # Média Lenta


        # Pega as últimas Moving Average
        last_ma_fast = self.stock_data['ma_fast'].iloc[-1]
        last_ma_slow = self.stock_data['ma_slow'].iloc[-1]

        # Toma a decisão, baseada na posição da média móvel
        # (False = Vender, True = Comprar)
        ma_trade_decision = last_ma_fast > last_ma_slow

        print('-----')
        print(f'Estratégia executada: Média Móvel')
        print(f'{self.operation_code}: {last_ma_fast:.3f} - Última Média Rápida \n {last_ma_slow:.3f} - Última Média Lenta')
        print(f'Decisão de posição: {"Comprar" if ma_trade_decision == True else "Vender"}')
        print('-----')

        return ma_trade_decision

    def getBolingerBandsTradeStrategy(self, window = 20, factor = 2):
        # Executa a estratégia de bollinger bands

        self.stock_data['bb_mean'] = self.stock_data['close_price'].rolling(window=window).mean()
        self.stock_data['bb_std'] = self.stock_data['close_price'].rolling(window=window).std()
        self.stock_data['bb_upper'] = self.stock_data['bb_mean'] + factor * self.stock_data['bb_std']
        self.stock_data['bb_lower'] = self.stock_data['bb_mean'] - factor * self.stock_data['bb_std']

        bb_trade_decision = self.stock_data['bb_lower'].iloc[-1] > self.stock_data['close_price'].iloc[-1]  # True = Comprar

        print('-----')
        print(f'Estratégia executada: Bollinger Bands')
        print(f'{self.operation_code}: {self.stock_data["bb_mean"].iloc[-1]:.3f} - Média Bollinger \n {self.stock_data["bb_upper"].iloc[-1]:.3f} - Bollinger Superior \n {self.stock_data["bb_lower"].iloc[-1]:.3f} - Bollinger Inferior \n {self.stock_data["close_price"].iloc[-1]:.3f} - Valor Atual')
        print(f'Decisão de posição: {"Comprar" if bb_trade_decision == True else "Vender"}')
        print('-----')


        return bb_trade_decision

    def getMovingAverageVergenceTradeStrategy(self, fast_window=7, slow_window=40):
        # Executa a estratégia de média móvel com volatilidade e gradiente


        self.stock_data['ma_fast'] = self.stock_data['close_price'].rolling(window=fast_window).mean()
        self.stock_data['ma_slow'] = self.stock_data['close_price'].rolling(window=slow_window).mean()
        self.stock_data['volatility'] = self.stock_data['close_price'].rolling(window=slow_window).std()
        last_ma_fast = self.stock_data['ma_fast'].iloc[-1]
        last_ma_slow = self.stock_data['ma_slow'].iloc[-1]
        prev_ma_slow = self.stock_data['ma_slow'].iloc[-2]
        prev_ma_fast = self.stock_data['ma_fast'].iloc[-2]

        last_volatility = self.stock_data['volatility'].iloc[-1]
        volatility = self.stock_data['volatility'][len(self.stock_data) - slow_window:].mean()  # Média da volatilidade dos últimos n valores
        fast_gradient = last_ma_fast - prev_ma_fast
        slow_gradient = last_ma_slow - prev_ma_slow

        current_difference = last_ma_fast - last_ma_slow


        ma_trade_decision = False

        if current_difference > volatility * self.volatility_factor and last_volatility < volatility: # Comprar com base em volatilidade e gradiente
            if last_ma_fast > last_ma_slow and fast_gradient > slow_gradient and last_ma_fast < last_ma_slow:
                ma_trade_decision = True
            elif last_ma_fast > last_ma_slow and fast_gradient > slow_gradient and last_ma_fast > last_ma_slow:
                ma_trade_decision = True
            elif fast_gradient > 0 and fast_gradient < slow_gradient and last_ma_fast > last_ma_slow:
                ma_trade_decision = False

        elif last_volatility > volatility:  # Vender com base em volatilidade
            if self.stock_data['ma_fast'].iloc[-3] > self.stock_data['ma_fast'].iloc[-2] and self.stock_data['ma_slow'].iloc[-3] > self.stock_data['ma_slow'].iloc[-2]:
                ma_trade_decision = False

        print('-----')
        print(f'Estratégia executada: Moving Average com Volatilidade + Gradiente')
        print(f'{self.operation_code}: {last_ma_fast:.3f} - Última Média Rápida \n {last_ma_slow:.3f} - Última Média Lenta')
        print(f'Última Volatilidade: {last_volatility:.3f} \\ Média da Volatilidade: {volatility:.3f}')
        print(f'Diferença Atual: {current_difference:.3f}')
        print(f'Gradiente rápido: {fast_gradient:.3f} ({ "Subindo" if fast_gradient > 0 else "Descendo" })')
        print(f'Gradiente lento: {slow_gradient:.3f} ({ "Subindo" if slow_gradient > 0 else "Descendo" })')
        print(f'Decisão: {"Comprar" if ma_trade_decision == True else "Vender"}')
        print('-----')


        return ma_trade_decision


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
        # Compra a ação
        if self.actual_trade_position == False: # Se a posição for vendida

            order_buy = self.client_binance.create_order(
                
                symbol = self.operation_code,
                side = SIDE_BUY,
                type = ORDER_TYPE_MARKET,
                quantity = self.traded_quantity,
            )
            self.actual_trade_position = True # Define posição como comprada

            createLogOrder(order_buy) # Cria um log
            return order_buy # Retorna a ordem

        else: # Se ocorreu algum erro
            logging.warning('Erro ao comprar')
            print('Erro ao comprar')
            return False

    def sellStock(self):
        # Vende a ação

        if self.actual_trade_position == True:  # Se a posição for comprada

            order_sell = self.client_binance.create_order(
                symbol = self.operation_code,
                side = SIDE_SELL,
                type = ORDER_TYPE_MARKET,
                quantity = int(self.last_stock_account_balance * 1000) / 1000,
            )
            self.actual_trade_position = False # Define posição como vendida

            createLogOrder(order_sell) # Cria um log
            return order_sell # Retorna a ordem

        else:  # Se ocorreu algum erro
            logging.warning('Erro ao vender')
            print('Erro ao vender')
            return False

    def execute(self):
        # Atualiza todos os dados

        self.updateAllData()

        print(f'Executado: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}') # Adiciona o horário atual
        print(f'Posição atual: {"Comprado" if MaTrader.actual_trade_position else "Vendido" }')
        print(f'Balanço atual: {MaTrader.last_stock_account_balance} ({self.stock_code})')


        # Executa a estratégia de média móvel

        ma_trade_decision = self.getMovingAverageTradeStrategy()

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
    #MaTrader.sellStock()