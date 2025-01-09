import pandas as pd
import numpy as np 

# strategies.py
class TradingStrategies:
     def __init__(self, stock_data, volume_threshold=1.5, rsi_period=14, rsi_upper=70, rsi_lower=30, stop_loss=0.05, stop_gain=0.10):
        self.stock_data = stock_data
        self.volume_threshold = volume_threshold  # Fator de comparação com a média de volume
        self.rsi_period = rsi_period
        self.rsi_upper = rsi_upper
        self.rsi_lower = rsi_lower
        self.stop_loss = stop_loss  # Percentual de Stop-Loss
        self.stop_gain = stop_gain  # Percentual de Stop-Gain
        self.entry_price = None  # Inicializa o preço de entrada como None

     def set_entry_price(self, price):
        self.entry_price = price  # Define o preço de entrada
        print(f"Preço de entrada registrado: {price:.3f}")

     def get_entry_price(self):
        if self.entry_price is not None:
            return self.entry_price
        else:
            raise ValueError("Preço de entrada não definido. Certifique-se de registrar o preço de entrada ao executar uma compra.")

     def calculate_rsi(self):
        delta = self.stock_data['close_price'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.rsi_period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.rsi_period).mean()
        rs = gain / loss
        self.stock_data['rsi'] = 100 - (100 / (1 + rs))

     def enhancedMovingAverageStrategy(self, fast_window=7, slow_window=40, volume_window=20, rsi_upper=70, rsi_lower=30):
      # Calcula as Médias Móveis
      self.stock_data['ma_fast'] = self.stock_data['close_price'].rolling(window=fast_window).mean()
      self.stock_data['ma_slow'] = self.stock_data['close_price'].rolling(window=slow_window).mean()

      # Calcula o Volume Médio
      self.stock_data['volume_mean'] = self.stock_data['volume'].rolling(window=volume_window).mean()
      last_volume = self.stock_data['volume'].iloc[-1]
      avg_volume = self.stock_data['volume_mean'].iloc[-1]

      # Calcula o RSI
      self.calculatex_rsi()
      last_rsi = self.stock_data['rsi'].iloc[-1]

      # RSI Dinâmico
      rsi_std = self.stock_data['rsi'].rolling(window=self.rsi_period).std()
      dynamic_rsi_upper = self.stock_data['rsi'].rolling(window=self.rsi_period).mean() + rsi_std
      dynamic_rsi_lower = self.stock_data['rsi'].rolling(window=self.rsi_period).mean() - rsi_std

      # Pega as últimas Moving Average
      last_ma_fast = self.stock_data['ma_fast'].iloc[-1]
      last_ma_slow = self.stock_data['ma_slow'].iloc[-1]

      # Preço atual e preço de entrada
      current_price = self.stock_data['close_price'].iloc[-1]
      entry_price = self.get_entry_price()
      print(f'Preço Atual: {current_price:.3f}')
      entry_price = None

      # Stop-loss e Stop-gain (se houver preço de entrada)
      if entry_price is not None:
       stop_loss_price = entry_price * (1 - self.stop_loss)
       stop_gain_price = entry_price * (1 + self.stop_gain)
      else:
        stop_loss_price = None
        stop_gain_price = None


      # Lógica de decisão com filtros e gerenciamento de risco
      ma_trade_decision = last_ma_fast > last_ma_slow  # Sinal principal (cruzamento de médias)
      volume_confirmation = last_volume > avg_volume * self.volume_threshold
      rsi_confirmation = last_rsi < dynamic_rsi_lower.iloc[-1] if ma_trade_decision else last_rsi > dynamic_rsi_upper.iloc[-1]


      trade_decision = (
      ma_trade_decision and
      volume_confirmation and
      rsi_confirmation and
      (current_price > stop_loss_price if entry_price is not None else True) and  # Verifica stop-loss se houver entrada
      (current_price < stop_gain_price if entry_price is not None else True)       # Verifica stop-gain se houver entrada
      )

      # Imprime os resultados
      print('-----')
      print(f'Estratégia executada: Enhanced Média Móvel com Volume, RSI, Stop-Loss e Stop-Gain')
      print(f'MA Rápida: {last_ma_fast:.3f} - MA Lenta: {last_ma_slow:.3f}')
      print(f'Volume Atual: {last_volume:.3f} - Volume Médio: {avg_volume:.3f}')
      print(f'RSI Atual: {last_rsi:.3f}')
      print(f'Preço Atual: {current_price:.3f}')
      print(f'Preço de Entrada: {entry_price:.3f}' if entry_price is not None else "Preço de Entrada não definido")
      print(f'Stop-Loss: {stop_loss_price:.3f} - Stop-Gain: {stop_gain_price:.3f}' if stop_loss_price is not None else "Stop-Loss e Stop-Gain não definidos")
      print(f'Confirmação de Volume: {"Sim" if volume_confirmation else "Não"}')
      print(f'Confirmação de RSI: {"Sim" if rsi_confirmation else "Não"}')
      print(f'Decisão de Posição: {"Comprar" if trade_decision else "Vender"}')
      print('-----')
      
      return trade_decision

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