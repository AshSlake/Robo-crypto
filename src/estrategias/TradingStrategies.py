from email import message
import pandas as pd
import numpy as np 
from logger import erro_logger, trade_logger, bot_logger


# strategies.py
class estrategies:
     def __init__(self, stock_data, volume_threshold=1.5, rsi_period=14, rsi_upper=70, rsi_lower=30, stop_loss=0.05, stop_gain=0.10, operation_code = None, actual_trade_position = None):
        self.stock_data = stock_data
        self.volume_threshold = volume_threshold
        self.rsi_period = rsi_period
        self.rsi_upper = rsi_upper
        self.rsi_lower = rsi_lower
        self.stop_loss = stop_loss
        self.stop_gain = stop_gain
        self.entry_price = None
        self.operation_code = operation_code # Adicione o código de operação
        self.actual_trade_position = actual_trade_position

     def set_entry_price(self, price):
        self.entry_price = price  # Define o preço de entrada
        print(f"Preço de entrada registrado: {price:.3f}")

     def get_entry_price(self):
        if self.entry_price is not None:
            return self.entry_price
        else:
            raise ValueError("Preço de entrada não definido. Certifique-se de registrar o preço de entrada ao executar uma compra.")

     def calculate_rsi(self, period=14):
        delta = self.stock_data['close_price'].diff()
        gain = delta.mask(delta < 0, 0)
        loss = -delta.mask(delta > 0, 0)

        avg_gain = gain.rolling(window=period, min_periods=period).mean()
        avg_loss = loss.rolling(window=period, min_periods=period).mean()

        rs = avg_gain / avg_loss
        self.stock_data['rsi'] = 100 - (100 / (1 + rs))

     def check_stop_loss(self, current_price, entry_price, stop_loss_percentage):
         return current_price <= entry_price * (1 - stop_loss_percentage)

     def check_take_profit(self, current_price, entry_price, take_profit_percentage):
         return current_price >= entry_price * (1 + take_profit_percentage)
        
     def message_bot_logger_info(self, message):
         bot_logger.info(message)

     def enhancedMovingAverageStrategy(self, fast_window=7, slow_window=40, volume_window=20):
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

      if trade_decision and not self.actual_trade_position:
            self.set_entry_price(current_price)


      if self.actual_trade_position:
            if self.check_stop_loss(current_price, self.entry_price, self.stop_loss):
                trade_decision = False  # Força a venda para acionar o stop-loss
                self.set_entry_price(None)
            elif self.check_take_profit(current_price, self.entry_price, self.stop_gain):
                trade_decision = False # Força a venda para acionar o take-profit
                self.set_entry_price(None)

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

        message = (
            f'{'---------------'}\n'
            f'Estratégia executada: Média Móvel\n'
            f'{self.operation_code}: {last_ma_fast:.3f} - Última Média Rápida \n {last_ma_slow:.3f} - Última Média Lenta'
            f'Decisão de posição: {"Comprar" if ma_trade_decision == True else "Vender"}\n'
            f'{'---------------'}\n'
        )

        bot_logger.info(message)


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

     def getMovingAverageVergenceTradeStrategy(self, fast_window=7, slow_window=40, volatility_factor=0.8):
       try:
        
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

        if current_difference > volatility * volatility_factor and last_volatility < volatility:
                if last_ma_fast > last_ma_slow and fast_gradient > slow_gradient:
                    ma_trade_decision = True

        elif last_volatility > volatility:
                if self.stock_data['ma_fast'].iloc[-3] > self.stock_data['ma_fast'].iloc[-2] and self.stock_data['ma_slow'].iloc[-3] > self.stock_data['ma_slow'].iloc[-2]:
                    ma_trade_decision = False

        print('-----')
        print(f'Estratégia executada: Moving Average com Volatilidade + Gradiente')
        print(f'{self.operation_code}: {last_ma_fast:.3f} - Última Média Rápida \n {last_ma_slow:.3f} - Última Média Lenta')
        print(f'Última Volatilidade: {last_volatility:.3f}')
        print(f'Média da Volatilidade: {volatility:.3f}')
        print(f'Diferença Atual das medias moveis: {current_difference:.3f}')
        print(f'Gradiente rápido: {fast_gradient:.3f} ({ "Subindo" if fast_gradient > 0 else "Descendo" })')
        print(f'Gradiente lento: {slow_gradient:.3f} ({ "Subindo" if slow_gradient > 0 else "Descendo" })')
        print(f'Decisão: {"Comprar" if ma_trade_decision == True else "Vender"}')
        print('-----')

        message = (
           f'{'---------------'}\n'
           f'Estratégia executada: Moving Average com Volatilidade + Gradiente\n'
           f'{self.operation_code}: {last_ma_fast:.3f} - Última Média Rápida \n {last_ma_slow:.3f} - Última Média Lenta'
           f'Última Volatilidade: {last_volatility:.3f} \\ Média da Volatilidade: {volatility:.3f}'
           f'Diferença Atual: {current_difference:.3f}'
           f'Gradiente rápido: {fast_gradient:.3f} ({ "Subindo" if fast_gradient > 0 else "Descendo" })'
           f'Gradiente lento: {slow_gradient:.3f}'
           f'Decisão: {"Comprar" if ma_trade_decision == True else "Vender"}\n'
           f'{'---------------'}\n'
        )
        bot_logger.info(message)
                                

       except IndexError:
            print("Erro: Dados insuficientes para calcular a estratégia Moving Average Vergence.")
            return False

       return ma_trade_decision
     
     def getMovingAverageVergenceTradeStrategyVersion2(self, fast_window=7, slow_window=40, volatility_factor=2.0, risk_percentage=1.0, take_profit_factor=2.0):
        try:
            # Calcula as médias móveis e a volatilidade
            self.stock_data['ma_fast'] = self.stock_data['close_price'].rolling(window=fast_window).mean()
            self.stock_data['ma_slow'] = self.stock_data['close_price'].rolling(window=slow_window).mean()
            self.stock_data['volatility'] = self.stock_data['close_price'].rolling(window=slow_window).std()

            last_ma_fast = self.stock_data['ma_fast'].iloc[-1]
            last_ma_slow = self.stock_data['ma_slow'].iloc[-1]
            prev_ma_fast = self.stock_data['ma_fast'].iloc[-2]
            prev_ma_slow = self.stock_data['ma_slow'].iloc[-2]
            last_volatility = self.stock_data['volatility'].iloc[-1]
            volatility = self.stock_data['volatility'][len(self.stock_data) - slow_window:].mean()

            fast_gradient = last_ma_fast - prev_ma_fast
            slow_gradient = last_ma_slow - prev_ma_slow
            current_difference = last_ma_fast - last_ma_slow

            # Obtém dados de Klines para calcular o volume médio
            klines = self.client_binance.get_klines(
                symbol=self.operation_code,
                interval=self.candle_period,
                limit=fast_window
            )
            klines_array = np.array(klines)
            volume_mean = np.mean(klines_array[:, 5].astype(float))

            # Decisão de trade
            ma_trade_decision = False
            if (current_difference > volatility * volatility_factor and 
                last_volatility < volatility and 
                last_ma_fast > last_ma_slow and 
                fast_gradient > slow_gradient and
                volume_mean > np.mean(klines_array[:, 5].astype(float))):
                ma_trade_decision = True
            elif last_volatility > volatility and prev_ma_fast > last_ma_fast and prev_ma_slow > last_ma_slow:
                ma_trade_decision = False

            # Gerenciamento de risco
            current_balance = self.get_balance()
            max_risk_amount = current_balance * (risk_percentage / 100)
            stop_loss_price = last_ma_slow - (volatility * volatility_factor)
            take_profit_price = last_ma_fast + (volatility * take_profit_factor)


            # Log da estratégia

            print('-----------------------------')
            print(f'Estratégia executada: Moving Average com Volatilidade + Gradiente')
            print(f'{self.operation_code}: {last_ma_fast:.3f} - Ultima Média Rápida | {last_ma_slow:.3f} - Ultima Média Lenta')
            print(f'Ultima Volatilidade: {last_volatility:.3f} | Média da Volatilidade: {volatility:.3f}')
            print(f'Diferença Atual: {current_difference:.3f}')
            print(f'Gradiente rápido: {fast_gradient:.3f} ({ "Subindo" if fast_gradient > 0 else "Descendo" })')
            print(f'Gradiente lento: {slow_gradient:.3f} ({ "Subindo" if slow_gradient > 0 else "Descendo" })')
            print(f'Volume Médio (últimos {fast_window}): {volume_mean:.2f}')
            print(f'Stop Loss: {stop_loss_price:.3f}, Take Profit: {take_profit_price:.3f}')
            print(f'Decisão: {"Comprar" if ma_trade_decision else "Vender"}')
            print('-----------------------------')

            message = (
                f'---------------\n'
                f'Estratégia executada: Moving Average com Volatilidade + Gradiente\n'
                f'{self.operation_code}: {last_ma_fast:.3f} - Última Média Rápida | {last_ma_slow:.3f} - Última Média Lenta\n'
                f'Última Volatilidade: {last_volatility:.3f} | Média da Volatilidade: {volatility:.3f}\n'
                f'Diferença Atual: {current_difference:.3f}\n'
                f'Gradiente rápido: {fast_gradient:.3f} ({ "Subindo" if fast_gradient > 0 else "Descendo" })\n'
                f'Gradiente lento: {slow_gradient:.3f} ({ "Subindo" if slow_gradient > 0 else "Descendo" })\n'
                f'Volume Médio (últimos {fast_window}): {volume_mean:.2f}\n'
                f'Stop Loss: {stop_loss_price:.3f}, Take Profit: {take_profit_price:.3f}\n'
                f'Decisão: {"Comprar" if ma_trade_decision else "Vender"}\n'
                f'---------------\n'
            )
            bot_logger.info(message)


            return ma_trade_decision, stop_loss_price, take_profit_price

        except (IndexError, KeyError) as e:
            erro_logger.exception(f"Erro na estratégia Moving Average Vergence: {e}")
            return False, None, None
        except Exception as e:
            erro_logger.exception(f"Outro erro na estratégia Moving Average Vergence: {e}")
            return False, None, None