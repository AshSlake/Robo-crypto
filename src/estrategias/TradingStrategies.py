from email import message
import pandas as pd
import numpy as np
from functions.logger import erro_logger, bot_logger
from functions.RsiCalculationClass import TechnicalIndicators


# strategies.py
class estrategies:
    def __init__(
        self,
        stock_data,
        volume_threshold=1.5,
        rsi_period=5,
        rsi_upper=70,
        rsi_lower=30,
        stop_loss=0.05,
        stop_gain=0.10,
        operation_code=None,
        actual_trade_position=None,
    ):
        self.stock_data = stock_data
        self.volume_threshold = volume_threshold
        self.rsi_period = rsi_period
        self.rsi_upper = rsi_upper
        self.rsi_lower = rsi_lower
        self.stop_loss = stop_loss
        self.stop_gain = stop_gain
        self.entry_price = None
        self.operation_code = operation_code
        self.actual_trade_position = actual_trade_position
        self.indicators = TechnicalIndicators(stock_data, rsi_period)

    def message_bot_logger_info(self, message):
        bot_logger.info(message)

    def getMovingAverage(self, fast_window=7, slow_window=40):

        # Calcula as Médias Móveis Rápida e Lenta
        self.stock_data["ma_fast"] = (
            self.stock_data["close_price"].rolling(window=fast_window).mean()
        )  # Média Rápida
        self.stock_data["ma_slow"] = (
            self.stock_data["close_price"].rolling(window=slow_window).mean()
        )  # Média Lenta

        # Pega as últimas Moving Average
        last_ma_fast = self.stock_data["ma_fast"].iloc[-1]
        last_ma_slow = self.stock_data["ma_slow"].iloc[-1]

        # Toma a decisão, baseada na posição da média móvel
        # (False = Vender, True = Comprar)
        ma_trade_decision = last_ma_fast > last_ma_slow

        print("-----")
        print(f"Estratégia executada: Média Móvel")
        print(
            f"{self.operation_code}: {last_ma_fast:.3f} - Última Média Rápida \n {last_ma_slow:.3f} - Última Média Lenta"
        )
        print(
            f'Decisão de posição: {"Comprar" if ma_trade_decision == True else "Vender"}'
        )
        print("-----")

        message = (
            f"{'---------------'}\n"
            f"Estratégia executada: Média Móvel\n"
            f"{self.operation_code}: {last_ma_fast:.3f} - Última Média Rápida \n {last_ma_slow:.3f} - Última Média Lenta"
            f'Decisão de posição: {"Comprar" if ma_trade_decision == True else "Vender"}\n'
            f"{'---------------'}\n"
        )

        bot_logger.info(message)

        return ma_trade_decision

    def getBolingerBands(self, window=20, factor=2):
        # Executa a estratégia de bollinger bands

        self.stock_data["bb_mean"] = (
            self.stock_data["close_price"].rolling(window=window).mean()
        )
        self.stock_data["bb_std"] = (
            self.stock_data["close_price"].rolling(window=window).std()
        )
        self.stock_data["bb_upper"] = (
            self.stock_data["bb_mean"] + factor * self.stock_data["bb_std"]
        )
        self.stock_data["bb_lower"] = (
            self.stock_data["bb_mean"] - factor * self.stock_data["bb_std"]
        )

        bb_trade_decision = (
            self.stock_data["bb_lower"].iloc[-1]
            > self.stock_data["close_price"].iloc[-1]
        )  # True = Comprar

        print("-----")
        print(f"Estratégia executada: Bollinger Bands")
        print(
            f'{self.operation_code}: {self.stock_data["bb_mean"].iloc[-1]:.3f} - Média Bollinger \n {self.stock_data["bb_upper"].iloc[-1]:.3f} - Bollinger Superior \n {self.stock_data["bb_lower"].iloc[-1]:.3f} - Bollinger Inferior \n {self.stock_data["close_price"].iloc[-1]:.3f} - Valor Atual'
        )
        print(
            f'Decisão de posição: {"Comprar" if bb_trade_decision == True else "Vender"}'
        )
        print("-----")

        return bb_trade_decision

    def getMovingAverageVergenceRSI(
        self, fast_window=7, slow_window=40, volatility_factor=0.7
    ):
        try:
            hysteresis = 0.001  # Define a histerese
            growth_threshold = 2.0  # Detectar crescimento quando o gradiente é duas vezes maior que o valor anterior
            correction_threshold = (
                0.3  # Detectar correção quando o gradiente diminui pelo menos 0.3
            )

            self.stock_data["ma_fast"] = (
                self.stock_data["close_price"].rolling(window=fast_window).mean()
            )
            self.stock_data["ma_slow"] = (
                self.stock_data["close_price"].rolling(window=slow_window).mean()
            )
            self.stock_data["volatility"] = (
                self.stock_data["close_price"].rolling(window=slow_window).std()
            )
            last_ma_fast = self.stock_data["ma_fast"].iloc[-1]
            last_ma_slow = self.stock_data["ma_slow"].iloc[-1]
            prev_ma_slow = self.stock_data["ma_slow"].iloc[-2]
            prev_ma_fast = self.stock_data["ma_fast"].iloc[-2]

            # instanciar a instância da classe RSICalculationClass
            # Após calcular o RSI
            self.indicators.calculate_rsi()

            # Verifique se a coluna 'rsi' existe e pegue o último valor
            if "rsi" in self.stock_data:
                last_rsi = self.stock_data["rsi"].iloc[-1]
            else:
                raise ValueError(
                    "Erro: a coluna 'rsi' não foi encontrada em 'self.stock_data' após o cálculo."
                )

            last_rsi = self.stock_data["rsi"].iloc[-1]

            last_volatility = self.stock_data["volatility"].iloc[-1]
            volatility = self.stock_data["volatility"][
                len(self.stock_data) - slow_window :
            ].mean()  # Média da volatilidade dos últimos n valores
            fast_gradient = last_ma_fast - prev_ma_fast
            slow_gradient = last_ma_slow - prev_ma_slow

            current_difference = last_ma_fast - last_ma_slow
            volatility_by_purshase = volatility * volatility_factor

            # Calcula a diferença do gradiente rápido e lento
            fast_gradient_diff = last_ma_fast - prev_ma_fast
            slow_gradient_diff = last_ma_slow - prev_ma_slow

            # CONDIÇÕES DE COMPRA
            if (
                current_difference > volatility * volatility_factor
                and last_volatility < volatility
                and last_rsi < self.rsi_upper
            ):
                ma_trade_decision = True  # Sinal de compra
                print(
                    "Compra: Diferença atual maior que volatilidade ajustada, última volatilidade menor e RSI abaixo do limite superior."
                )

            elif (
                last_ma_fast > last_ma_slow + hysteresis
                and fast_gradient > slow_gradient
            ):
                ma_trade_decision = True  # Sinal de compra
                print(
                    "Compra: MA rápida maior que MA lenta ajustada por histerese, e gradiente rápido maior que o lento."
                )

            elif (
                last_ma_fast > last_ma_slow + hysteresis
                and last_volatility > (volatility / 2)
                and fast_gradient > slow_gradient
            ):
                ma_trade_decision = True  # Sinal de compra
                print(
                    "Compra: MA rápida maior que MA lenta ajustada por histerese, volatilidade anterior maior que a metade da volatilidade atual, e gradiente rápido maior que o lento."
                )

            elif (
                current_difference > volatility * volatility_factor
                and last_volatility > volatility
                and fast_gradient > slow_gradient
                and last_rsi > self.rsi_lower
            ):
                ma_trade_decision = True  # Sinal de compra
                print(
                    "Compra: Diferença atual maior que volatilidade ajustada, última volatilidade maior, gradiente rápido maior que o lento, e RSI acima do limite inferior."
                )

            elif (
                volatility > last_volatility
                and last_rsi > 60
                and fast_gradient > slow_gradient
            ):
                ma_trade_decision = True  # Sinal de compra
                print(
                    "Compra: Volatilidade anterior maior que a atual, RSI acima de 60%, e gradiente rápido maior que o lento."
                )

            # CONDIÇÕES DE VENDA
            elif last_ma_fast < last_ma_slow - hysteresis:
                ma_trade_decision = False  # Sinal de venda
                print(
                    "Venda: MA rápida cruzou abaixo da MA lenta ajustada por histerese."
                )

            elif last_ma_fast > last_ma_slow:
                if last_volatility > volatility:
                    if fast_gradient < slow_gradient:
                        ma_trade_decision = False  # Sinal de venda
                        print(
                            "Venda: MA rápida maior que a lenta, mas a volatilidade anterior é maior que a atual, e o gradiente rápido menor que o lento."
                        )

            elif last_rsi < self.rsi_lower:
                if fast_gradient < slow_gradient:
                    ma_trade_decision = False  # Sinal de venda
                    print(
                        "Venda: RSI abaixo do limite inferior e gradiente rápido menor que o lento."
                    )

            # Detectar crescimento rápido no gradiente rápido
            elif fast_gradient_diff > growth_threshold * prev_ma_fast:
                print(
                    f"Crescimento Rápido Detectado: O gradiente rápido aumentou significativamente para {fast_gradient_diff}."
                )
                # Após o crescimento rápido, verificar se está começando a corrigir
                if fast_gradient < prev_ma_fast - correction_threshold:
                    ma_trade_decision = False  # Sinal de venda ou alerta
                    print(
                        f"Correção Detectada: O gradiente rápido começou a corrigir, caindo para {fast_gradient}."
                    )
                else:
                    print(
                        "Espera: O gradiente rápido ainda está subindo ou não começou a corrigir significativamente."
                    )
            else:
                print(
                    "Sem Crescimento Rápido: O gradiente rápido não cresceu significativamente."
                )

            print("-----")
            print(
                f"Estratégia executada: Moving Average com Volatilidade + Gradiente + RSI"
            )
            print(
                f"{self.operation_code}:\n {last_ma_fast:.3f} - Última Média Rápida \n {last_ma_slow:.3f} - Última Média Lenta"
            )
            print(f"Última Volatilidade: {last_volatility:.3f}")
            print(f"Média da Volatilidade: {volatility:.3f}")
            print(f"Diferença Atual das medias moveis: {current_difference:.3f}")
            print(f"volatibilidade * volatilidade_factor: {volatility_by_purshase:.3f}")
            print(f"Último RSI: {last_rsi:.3f}")
            print(
                f'Gradiente rápido: {fast_gradient:.3f} ({ "Subindo" if fast_gradient > 0 else "Descendo" })'
            )
            print(
                f'Gradiente lento: {slow_gradient:.3f} ({ "Subindo" if slow_gradient > 0 else "Descendo" })'
            )
            print(f'Decisão: {"Comprar" if ma_trade_decision == True else "Vender" }')
            print("-----")

            message = (
                f"{'---------------'}\n"
                f"Estratégia executada: Moving Average com Volatilidade + Gradiente\n"
                f"{self.operation_code}: {last_ma_fast:.3f} - Última Média Rápida \n {last_ma_slow:.3f} - Última Média Lenta"
                f"Última Volatilidade: {last_volatility:.3f} \\ Média da Volatilidade: {volatility:.3f}"
                f"Diferença Atual: {current_difference:.3f}"
                f"Último RSI: {last_rsi:.3f}\n"
                f'Gradiente rápido: {fast_gradient:.3f} ({ "Subindo" if fast_gradient > 0 else "Descendo" })'
                f"Gradiente lento: {slow_gradient:.3f}"
                f'Decisão: {"Comprar" if ma_trade_decision == True else "Vender"}\n'
                f"{'---------------'}\n"
            )
            bot_logger.info(message)

        except IndexError:
            print(
                "Erro: Dados insuficientes para calcular a estratégia Moving Average Vergence."
            )
            return False

        return ma_trade_decision

    def getMovingAverageVergence2(
        self,
        fast_window=7,
        slow_window=40,
        volatility_factor=0.7,
        risk_percentage=1.0,
        take_profit_factor=2.0,
    ):
        try:
            # Calcula as médias móveis e a volatilidade
            self.stock_data["ma_fast"] = (
                self.stock_data["close_price"].rolling(window=fast_window).mean()
            )
            self.stock_data["ma_slow"] = (
                self.stock_data["close_price"].rolling(window=slow_window).mean()
            )
            self.stock_data["volatility"] = (
                self.stock_data["close_price"].rolling(window=slow_window).std()
            )

            last_ma_fast = self.stock_data["ma_fast"].iloc[-1]
            last_ma_slow = self.stock_data["ma_slow"].iloc[-1]
            prev_ma_fast = self.stock_data["ma_fast"].iloc[-2]
            prev_ma_slow = self.stock_data["ma_slow"].iloc[-2]
            last_volatility = self.stock_data["volatility"].iloc[-1]
            volatility = self.stock_data["volatility"][
                len(self.stock_data) - slow_window :
            ].mean()

            fast_gradient = last_ma_fast - prev_ma_fast
            slow_gradient = last_ma_slow - prev_ma_slow
            current_difference = last_ma_fast - last_ma_slow

            # Obtém dados de Klines para calcular o volume médio
            klines = self.client_binance.get_klines(
                symbol=self.operation_code,
                interval=self.candle_period,
                limit=fast_window,
            )
            klines_array = np.array(klines)
            volume_mean = np.mean(klines_array[:, 5].astype(float))

            # Decisão de trade
            ma_trade_decision = False
            if (
                current_difference > volatility * volatility_factor
                and last_volatility < volatility
                and last_ma_fast > last_ma_slow
                and fast_gradient > slow_gradient
                and volume_mean > np.mean(klines_array[:, 5].astype(float))
            ):
                ma_trade_decision = True
            elif (
                last_volatility > volatility
                and prev_ma_fast > last_ma_fast
                and prev_ma_slow > last_ma_slow
            ):
                ma_trade_decision = False

            # Gerenciamento de risco
            current_balance = self.get_balance()
            max_risk_amount = current_balance * (risk_percentage / 100)
            stop_loss_price = last_ma_slow - (volatility * volatility_factor)
            take_profit_price = last_ma_fast + (volatility * take_profit_factor)

            # Log da estratégia

            print("-----------------------------")
            print(f"Estratégia executada: Moving Average com Volatilidade + Gradiente")
            print(
                f"{self.operation_code}: {last_ma_fast:.3f} - Ultima Média Rápida | {last_ma_slow:.3f} - Ultima Média Lenta"
            )
            print(
                f"Ultima Volatilidade: {last_volatility:.3f} | Média da Volatilidade: {volatility:.3f}"
            )
            print(f"Diferença Atual: {current_difference:.3f}")
            print(
                f'Gradiente rápido: {fast_gradient:.3f} ({ "Subindo" if fast_gradient > 0 else "Descendo" })'
            )
            print(
                f'Gradiente lento: {slow_gradient:.3f} ({ "Subindo" if slow_gradient > 0 else "Descendo" })'
            )
            print(f"Volume Médio (últimos {fast_window}): {volume_mean:.2f}")
            print(
                f"Stop Loss: {stop_loss_price:.3f}, Take Profit: {take_profit_price:.3f}"
            )
            print(f'Decisão: {"Comprar" if ma_trade_decision else "Vender"}')
            print("-----------------------------")

            message = (
                f"---------------\n"
                f"Estratégia executada: Moving Average com Volatilidade + Gradiente\n"
                f"{self.operation_code}: {last_ma_fast:.3f} - Última Média Rápida | {last_ma_slow:.3f} - Última Média Lenta\n"
                f"Última Volatilidade: {last_volatility:.3f} | Média da Volatilidade: {volatility:.3f}\n"
                f"Diferença Atual: {current_difference:.3f}\n"
                f'Gradiente rápido: {fast_gradient:.3f} ({ "Subindo" if fast_gradient > 0 else "Descendo" })\n'
                f'Gradiente lento: {slow_gradient:.3f} ({ "Subindo" if slow_gradient > 0 else "Descendo" })\n'
                f"Volume Médio (últimos {fast_window}): {volume_mean:.2f}\n"
                f"Stop Loss: {stop_loss_price:.3f}, Take Profit: {take_profit_price:.3f}\n"
                f'Decisão: {"Comprar" if ma_trade_decision else "Vender"}\n'
                f"---------------\n"
            )
            bot_logger.info(message)

            return ma_trade_decision, stop_loss_price, take_profit_price

        except (IndexError, KeyError) as e:
            erro_logger.exception(f"Erro na estratégia Moving Average Vergence: {e}")
            return False, None, None
        except Exception as e:
            erro_logger.exception(
                f"Outro erro na estratégia Moving Average Vergence: {e}"
            )
            return False, None, None
