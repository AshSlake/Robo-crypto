from decimal import Decimal
from http import client
import os
import pandas as pd

from werkzeug import Client
from db.neonDbConfig import (
    get_last_gradients_from_db,
    save_gradients_to_db_with_limit,
)


from functions.InteligenciaArtificial.GeminiTradingBot import GeminiTradingBot
from functions.binance.getActualTradePositionForBinance import (
    getActualTradePositionForBinance,
)
from functions.indicadores.calculate_fast_gradients import calculate_fast_gradients
from functions.indicadores.calculate_gradient_percentage_change import (
    calculate_gradient_percentage_change,
)
from functions.calculators.calculate_jump_threshold import calculate_jump_threshold
from functions.indicadores.calculate_moving_average import calculate_moving_average
from functions.calculators.calculate_recent_growth_value import (
    calculate_recent_growth_value,
)
from functions.calculators.calculate_support_resistance_from_prices import (
    calculate_support_resistance_from_prices,
)
from functions.detect_new_price_jump import detect_new_price_jump
from functions.get_current_price import get_current_price
from functions.get_recent_prices import get_recent_prices
from functions.indicadores.macd import calculate_macd, get_historical_data
from functions.logger import erro_logger, bot_logger
from functions.indicadores.RsiCalculationClass import TechnicalIndicators
from functions.CandlestickDataExtractor import CandlestickDataExtractor
from binance.client import Client

from functions.machine_learning.coletor_dados.DataCollector import DataCollector
from functions.update_fast_gradients import update_fast_gradients
from functions.machine_learning.gradient_Boosting.result import Result as result

api_key = os.getenv("BINANCE_API_KEY")
secret_key = os.getenv("BINANCE_SECRET_KEY")


class getMovingAverageVergenceRSI:
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
        current_price_from_buy_order=None,
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

        # Variáveis adicionais
        self.indicators = TechnicalIndicators(stock_data, rsi_period)
        self.last_fast_gradient = None
        self.last_slow_gradient = None
        self.prev_rsi = None
        self.client_binance = Client(api_key, secret_key)
        self.alerta_de_crescimento_rapido = False
        self.fast_gradients = []
        self.current_price = Decimal
        self.current_price_from_buy_order = current_price_from_buy_order
        self.interval = Client.KLINE_INTERVAL_15MINUTE
        self.recent_average = None
        self.state_after_correction = None
        self.percentage_fromUP_fast_gradient = None
        self.percentage_fromDOWN_fast_gradient = None
        self.max_price_resistenceZone = None
        self.last_max_price_down_resistanceZone = 0
        self.min_price_supportZone = None
        self.last_min_price_up_supportZone = 0
        self.volatility_tracker = []
        self.current_volume = None
        self.min_gradient_difference = 0.02
        self.actual_trade_position = None
        self.lastHistograma = None
        self.actual_trade_position = getActualTradePositionForBinance(
            self, self.operation_code
        )

    def getMovingAverageVergenceRSI(
        self,
        fast_window=7,
        slow_window=40,
        volatility_factor=0.7,
        initial_purchase_price=100.0,
        hysteresis=0.001,
        growth_threshold=2.0,
    ):
        try:
            growth_threshold = 0.002  # Detectar crescimento quando o gradiente é duas vezes maior que o valor anterior
            correction_threshold = (
                0.08  # Detectar correção quando o gradiente diminui pelo menos 0.3
            )
            ma_trade_decision = None
            stop_loss_percentage = 0.05  # 5% abaixo do preço de compra
            self.current_price = get_current_price(self.operation_code)

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
                self.prev_rsi = self.stock_data["rsi"].iloc[-2]
            else:
                raise ValueError(
                    "Erro: a coluna 'rsi' não foi encontrada em 'self.stock_data' após o cálculo."
                )

            last_rsi = self.stock_data["rsi"].iloc[-1]

            last_volatility = self.stock_data["volatility"].iloc[-1]
            volatility = self.stock_data["volatility"][
                len(self.stock_data) - slow_window :
            ].mean()  # Média da volatilidade dos últimos n valores

            hysteresis = max(0.01, volatility * 0.1)

            fast_gradient = last_ma_fast - prev_ma_fast
            slow_gradient = last_ma_slow - prev_ma_slow

            gradient_difference = fast_gradient - slow_gradient

            # Salvar os gradientes no banco de dados com limite
            save_gradients_to_db_with_limit(fast_gradient, slow_gradient, limit=10)

            # Recuperar os dois últimos gradientes para comparação
            gradients_from_db = get_last_gradients_from_db()

            if gradients_from_db:
                self.last_fast_gradient = gradients_from_db["prev_fast_gradient"]
                self.last_slow_gradient = gradients_from_db["prev_slow_gradient"]

                # Comparar os gradientes
                # if self.last_fast_gradient is not None:
                #    print(
                #        f"Comparação - Gradiente rápido anterior: {self.last_fast_gradient:.3f}, atual: {fast_gradient:.3f}"
                #    )
                # else:
                #    print("Primeira execução, sem gradiente anterior para comparar.")
            else:
                print("Nenhum gradiente encontrado no banco de dados.")

            current_difference = last_ma_fast - last_ma_slow
            volatility_by_purshase = volatility * volatility_factor

            # Calcular o preço de stop-loss
            stop_loss_price = Decimal(self.current_price_from_buy_order) * Decimal(
                1 - stop_loss_percentage
            )
            print(f"Preço de stop-loss: {stop_loss_price:.2f}")

            # Obter dados recentes de preços
            prices, recent_volumes = get_recent_prices(
                self, symbol=self.operation_code, interval=self.interval, limit=1000
            )

            self.current_volume = recent_volumes[-1]
            print(f"Volume recente: {self.current_volume:.3f}")

            # Definin zonas de suporte e resistência
            support_resistance = calculate_support_resistance_from_prices(prices)
            self.min_price_supportZone = support_resistance[
                "support"
            ]  # Preço mínimo zona de suporte
            self.max_price_resistenceZone = support_resistance[
                "resistance"
            ]  # Preço maximo zona de resistência

            # Atualizar as variáveis de  zonas de last_max_price_down_resistanceZone e last_min_price_up_supportZone
            if self.last_max_price_down_resistanceZone < self.current_price:
                self.last_max_price_down_resistanceZone = self.current_price
            if (
                self.last_min_price_up_supportZone > self.current_price
                or self.last_min_price_up_supportZone == 0
            ):
                self.last_min_price_up_supportZone = self.current_price

            print(f"Preço atual: {self.current_price:.2f}")
            print(f"Resistência: {self.max_price_resistenceZone:.2f}")
            print(f"Suporte: {self.min_price_supportZone:.2f}")
            print(
                f"zona de resistência recente: {self.last_max_price_down_resistanceZone:.2f}"
            )
            print(
                f"zona de suporte recente: {self.last_min_price_up_supportZone:.2f}\n"
            )

            # Calculando os fast_gradients na estratégia
            ma_fast_values = calculate_moving_average(self, prices, window=7)
            fast_gradients = calculate_fast_gradients(self, ma_fast_values)

            # Atualizar o buffer de gradientes rápidos
            latest_fast_gradient = fast_gradients[-1]
            update_fast_gradients(self, new_fast_gradient=latest_fast_gradient)

            # Calcula o jump_threshold com base nos preços e médias móveis rápidas
            jump_threshold = calculate_jump_threshold(
                self,
                current_price=self.current_price,
                ma_fast_values=ma_fast_values,
                factor=1.5,
            )

            # Calcula o valor médio dos gradientes rápidos recentes
            self.recent_average = calculate_recent_growth_value(
                self, fast_gradients, growth_threshold, prev_ma_fast
            )

            # Calcula o percentual de crescimento dos gradientes rápidos
            (
                self.percentage_fromUP_fast_gradient,
                self.percentage_fromDOWN_fast_gradient,
            ) = calculate_gradient_percentage_change(
                fast_gradient, self.last_fast_gradient
            )

            ma_gap = (
                last_ma_fast - last_ma_slow
            )  # Representa a diferença entre a média móvel rápida e a média móvel lenta.
            ma_gap_rate_of_change = (
                last_ma_fast - last_ma_slow
            ) / last_ma_slow  # Representa a taxa de mudança percentual do gap entre as médias móveis.
            rsi_rate_of_change = (
                last_rsi - self.prev_rsi
            ) / self.prev_rsi  # Representa a taxa de mudança percentual do RSI (Índice de Força Relativa).
            # Recuperar posição atual
            self.actual_trade_position = getActualTradePositionForBinance(
                self, self.operation_code
            )

            df = get_historical_data(
                symbol=self.operation_code, interval=self.interval, limit=500
            )
            macd_values = calculate_macd(df)
            self.lastHistograma = Decimal(macd_values["LastHistograma"])

            # Cálculo da taxa de crescimento do RSI
            rsi_rate_of_change = (
                (last_rsi - self.prev_rsi) / self.prev_rsi if self.prev_rsi != 0 else 0
            )

            # Cálculo da taxa de crescimento do histograma do MACD
            macd_histogram_rate_of_change = (
                Decimal(macd_values["Histograma"]) - self.lastHistograma
            ) / self.lastHistograma

            # CONDIÇÕES DE COMPRA
            # 1 - Confirmação de Tendência de Alta
            if (
                current_difference > volatility * volatility_factor
                and last_volatility < volatility
                and self.rsi_lower < last_rsi < self.rsi_upper
                and fast_gradient
                > slow_gradient  # Confirmando que o gradiente rápido está subindo
                and (
                    self.percentage_fromUP_fast_gradient
                    > 1.5 * self.percentage_fromDOWN_fast_gradient
                )  # Confirmando aceleração do gradiente
                and macd_values["MACD"]
                > macd_values["Signal"]  # MACD cruzando acima da linha de sinal
                and macd_values["Buy_Signal"]  # Sinal de compra pelo MACD
            ):
                ma_trade_decision = True
                message = (
                    f"\n{'-'*50}\n"
                    f"📈 **Sinal de COMPRA - Tendência de Alta Confirmada** 📈\n"
                    f"🔹 Diferença Atual: **{current_difference:.3f}**, maior que o limite ajustado ({volatility * volatility_factor:.3f}).\n"
                    f"🔹 Volatilidade atual ({volatility:.3f}) está abaixo da anterior ({last_volatility:.3f}), indicando estabilidade.\n"
                    f"🔹 RSI dentro da faixa desejada ({self.rsi_lower}-{self.rsi_upper}), sugerindo um momento ideal para compra.\n"
                    f"🔹 Gradiente rápido **{fast_gradient:.3f}** está subindo, confirmando tendência positiva.\n"
                    f"✅ Condições favoráveis detectadas para uma possível entrada no mercado!\n"
                    f"✅ MACD indica tendência de alta e confirma o sinal de compra!\n"
                    f"{'-'*50}\n"
                )
                print(message)
                bot_logger.info(message)

            # 2 - Divergência Positiva e Crescimento no RSI
            elif (
                ma_gap > hysteresis
                and ma_gap_rate_of_change > 0.02
                and current_difference < volatility * volatility_factor
                and last_volatility > volatility
                and self.percentage_fromUP_fast_gradient
                > self.percentage_fromDOWN_fast_gradient
                and last_rsi > self.rsi_lower
                and last_rsi < self.rsi_upper
                and rsi_rate_of_change > 0.01  # RSI em aumento
                and macd_values["MACD"]
                > macd_values["Signal"]  # MACD cruzando acima da linha de sinal
            ):
                ma_trade_decision = True
                message = (
                    f"\n{'-'*50}\n"
                    f"📊 **Sinal de COMPRA - Divergência Positiva Detectada** 📊\n"
                    f"🔹 MA rápida **{last_ma_fast:.3f}** acima da MA lenta **{last_ma_slow:.3f}**, superando histerese ({hysteresis:.3f}).\n"
                    f"🔹 Volatilidade anterior ({last_volatility:.3f}) é maior que a atual ({volatility:.3f}), indicando possível estabilização.\n"
                    f"🔹 RSI **{last_rsi:.3f}** está subindo, dentro do intervalo favorável ({self.rsi_lower}-{self.rsi_upper}).\n"
                    f"✅ Potencial reversão confirmada com aumento gradual no RSI e divergência positiva!\n"
                    f"✅ MACD confirma a divergência positiva e reforça o sinal de compra!\n"
                    f"{'-'*50}\n"
                )
                print(message)
                bot_logger.info(message)

            # 3 - Aceleração Agressiva do Gradiente e Volatilidade Elevada
            elif (
                self.percentage_fromUP_fast_gradient
                > 50 + (last_volatility * 10)  # Limite dinâmico
                and self.rsi_lower < last_rsi < self.rsi_upper  # RSI dentro de limites
                and gradient_difference
                > self.min_gradient_difference  # Diferença mínima entre gradientes
                and last_volatility
                > volatility * 1.2  # Volatilidade significativamente acima da média
                and macd_values["Histograma"] > 0  # MACD indicando força na tendências
            ):
                ma_trade_decision = True
                message = (
                    f"\n{'-'*50}\n"
                    f"🚀 **Sinal de COMPRA - Aceleração Forte do Gradiente** 🚀\n"
                    f"🔹 Gradiente rápido: **{fast_gradient:.3f}**, maior que lento: **{slow_gradient:.3f}**.\n"
                    f"🔹 RSI estável em **{last_rsi:.3f}**, dentro dos limites ({self.rsi_lower}-{self.rsi_upper}).\n"
                    f"🔹 Volatilidade significativamente elevada: **{last_volatility:.3f}**, acima da média ({volatility:.3f}).\n"
                    f"✅ Aceleração forte no preço detectada. Possível rompimento iminente!\n"
                    f"✅ Aceleração forte no preço e confirmação pelo MACD!\n"
                    f"{'-'*50}\n"
                )
                print(message)
                bot_logger.info(message)

            # 4 - Reversão de Tendência após Forte Queda
            elif (
                last_volatility < volatility
                and last_rsi < self.rsi_lower + hysteresis
                and last_rsi > 10
                and fast_gradient < slow_gradient
                and current_difference > volatility * volatility_factor
                and macd_values["Sell_Signal"] is False  # Evita sinais de venda do MACD
            ):
                message = (
                    f"\n{'-'*50}\n"
                    f"📉 **Sinal de COMPRA - Possível Reversão de Queda** 📉\n"
                    f"🔹 RSI extremamente baixo em **{last_rsi:.2f}**, indicando sobrevenda.\n"
                    f"🔹 Volatilidade atual **{volatility:.3f}** é maior que a anterior **{last_volatility:.3f}**.\n"
                    f"🔹 Diferença das médias móveis: **{current_difference:.3f}**, acima do limite ajustado ({volatility * volatility_factor:.3f}).\n"
                    f"🔹 Gradiente rápido **{fast_gradient:.3f}** está abaixo do gradiente lento **{slow_gradient:.3f}**.\n"
                    f"✅ Possível reversão de tendência! O mercado pode estar encontrando suporte.\n"
                    f"✅ MACD não indica venda, reforçando a possível reversão de tendência!\n"
                    f"{'-'*50}\n"
                )

                print(message)
                bot_logger.info(message)
                ma_trade_decision = True  # Sinal de compra

            # 5
            # Preço acima do Suporte mais Recente, RSI e MACD indicam crescimento
            elif (
                self.current_price
                > self.last_max_price_down_resistanceZone  # O preço atual deve ser maior que o suporte mais recente
                and rsi_rate_of_change
                > 0.01  # A taxa de crescimento do RSI está aumentando
                and macd_histogram_rate_of_change
                > 0.01  # A taxa de crescimento do histograma do MACD está aumentando
                and macd_values["MACD"]
                > macd_values["Signal"]  # MACD cruzando acima da linha de sinal
            ):
                ma_trade_decision = True
                message = (
                    f"\n{'-'*50}\n"
                    f"🚀 **Sinal de COMPRA - Condições Favoráveis Detectadas** 🚀\n"
                    f"🔹 O preço atual **{self.current_price:.3f}** está acima do suporte mais recente **{self.last_max_price_down_resistanceZone:.3f}**.\n"
                    f"🔹 O RSI está aumentando, com uma taxa de crescimento de **{rsi_rate_of_change:.3f}**.\n"
                    f"🔹 O histograma do MACD está em crescimento, com uma taxa de **{macd_histogram_rate_of_change:.3f}**.\n"
                    f"🔹 O MACD está cruzando acima da linha de sinal e o histograma é positivo, indicando força na tendência.\n"
                    f"✅ Condições ideais para uma possível compra!\n"
                    f"{'-'*50}\n"
                )
                print(message)
                bot_logger.info(message)

            # CONDIÇÕES DE VENDA
            # 1
            elif (
                fast_gradient < slow_gradient
                and self.percentage_fromDOWN_fast_gradient > 50
                and last_rsi > self.rsi_upper
                and self.current_price < self.last_max_price_down_resistanceZone
            ):
                ma_trade_decision = False  # Sinal de venda
                self.alerta_de_crescimento_rapido = False
                message = (
                    f"Venda: a porcentagem de decremento do gradiente rapido despencou mais que 30%\n"
                    f"Ultimo RSI está abaixo do limite superior e o preço atual está abaixo da zona de resistência recente.\n"
                    f"sugere um possível inicio de reversão para baixa.\n Realizando a venda.\n"
                )
                print(message)
                bot_logger.info(message)

            # 2
            elif (
                last_ma_fast < last_ma_slow - hysteresis
                and fast_gradient < slow_gradient
                and fast_gradient <= 0
                and self.alerta_de_crescimento_rapido == False
            ):
                ma_trade_decision = False  # Sinal de venda
                message = f"Venda: A MA rápida cruzou abaixo da MA lenta ajustada por histerese, sinalizando uma possível reversão de tendência para baixa.\n"
                print(message)
                bot_logger.info(message)
            # 3
            elif (
                last_ma_fast > last_ma_slow
                and last_volatility > volatility
                and fast_gradient < slow_gradient
                and last_rsi < self.rsi_lower
                and self.percentage_fromDOWN_fast_gradient > 30
                and self.alerta_de_crescimento_rapido == False
            ):
                ma_trade_decision = False  # Sinal de venda
                message = (
                    f"Venda: Apesar da MA rápida estar acima da lenta, a alta volatilidade e o gradiente rápido menor que o lento \n"
                    f"ou o RSI abaixo do limite inferior sugerem um risco de reversão. Melhor realizar vendas.\n"
                )
                print(message)
                bot_logger.info(message)
            # 4
            elif (
                fast_gradient < self.last_fast_gradient - hysteresis
                and last_rsi < self.prev_rsi - hysteresis
                and last_rsi < self.rsi_lower + hysteresis
                and self.percentage_fromDOWN_fast_gradient > 20
                and self.alerta_de_crescimento_rapido == False
            ):
                ma_trade_decision = False  # Sinal de venda
                message = (
                    f"Venda: O gradiente rápido diminuiu significativamente e o RSI abaixo do ultimo valor do RSI, \n"
                    f"indicando uma possível reversão de tendência para baixa.\n"
                )
                print(message)
                bot_logger.info(message)

            # 5
            # Verificar se o preço atual caiu abaixo do stop-loss
            elif self.current_price < stop_loss_price:
                ma_trade_decision = False  # Sinal de venda devido ao stop-loss
                message = (
                    f"Stop-Loss Ativado: O preço atual de {self.current_price:.3f} caiu abaixo do nível de stop-loss de {stop_loss_price:.2f}. \n"
                    f"Realizando venda para limitar as perdas.\n"
                )
                print(message)
                bot_logger.info(message)

            # 6
            elif (
                last_volatility < volatility
                and last_rsi < self.rsi_lower + hysteresis
                and last_rsi < 10
                and fast_gradient < slow_gradient
                and current_difference < volatility * volatility_factor
            ):
                message = (
                    f"A alta volatilidade diminuiu significativamente e o RSI ultrapassou o limite superior, \n"
                    f"indicando uma possível reversão de tendência para baixa.\n"
                    f"Realizando venda para limitar as perdas.\n"
                )
                print(message)
                bot_logger.info(message)
                ma_trade_decision = False  # Sinal de venda
            # 7
            # Detectar queda apos atingir preço maximo do preço
            elif (
                self.current_price < self.min_price_supportZone
                and fast_gradient < self.last_fast_gradient - hysteresis
                and self.percentage_fromDOWN_fast_gradient > 10
            ):
                ma_trade_decision = False  # Sinal de venda
                message = f"detectado queda apos atingir preço máximo do preço: O preço atual de {self.current_price:.3f} está abaixo do nível de preço máximo e caindo\n"
                print(message)
                bot_logger.info(message)
            # 8
            # Detectar crescimento rápido no gradiente rápido
            if self.recent_average > growth_threshold * prev_ma_fast:
                print(
                    f"\n ------------------ \n Crescimento Consistente Detectado: O gradiente médio recente aumentou significativamente, indicando uma forte tendência de alta.\n ------------------ \n"
                )
                message = f"Crescimento Consistente Detectado: O gradiente médio recente aumentou significativamente, indicando uma forte tendência de alta.\n"
                bot_logger.info(message)
                ma_trade_decision = True  # Sinal de compra
                self.alerta_de_crescimento_rapido = True

                # Após o crescimento rápido, verificar se está começando a corrigir
                if fast_gradient < self.last_fast_gradient - correction_threshold:
                    ma_trade_decision = False  # Sinal de venda
                    self.alerta_de_crescimento_rapido = (
                        False  # Desativar alerta de alta
                    )
                    self.state_after_correction = (
                        True  # Ativar estado de espera para nova alta
                    )
                    message = (
                        f"Correção Detectada: O gradiente rápido começou a corrigir, caindo de {self.last_fast_gradient:.5f} para {fast_gradient:.3f},\n "
                        f"indicando uma possível reversão ou ajuste no mercado."
                    )
                    print(message)
                    bot_logger.info(message)

                elif self.state_after_correction:
                    # Verificar se há uma continuação na alta
                    if detect_new_price_jump(
                        self, fast_gradient, prices, jump_threshold
                    ):
                        ma_trade_decision = True  # Confirmação de alta pós-correção
                        self.state_after_correction = False  # Resetar estado
                        message = f"Continuação da Alta Confirmada: O preço ou gradiente mostram um novo salto significativo, validando a retomada da alta.\n"
                        print(message)
                        bot_logger.info(message)
                    else:
                        message = f"Espera: Ainda não foi detectado um novo salto no preço ou gradiente. Continuar monitorando.\n"
                        print(message)
                        bot_logger.info(message)
            else:
                self.alerta_de_crescimento_rapido = False

            if ma_trade_decision == None:
                print("\n Nenhuma condição de compra ou venda atendida.")
                bot_logger.info("\n Nenhuma condição de compra ou venda atendida.")

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
                f"^indicador de tendencia de alta:\n"
                f"  - Media recente dos Gradientes rapidos: {self.recent_average:.3f}\n"
                f"  - Media necessaria para tendecia de alta: {growth_threshold * prev_ma_fast:.3f}\n"
                f"  - gradiente rapido maximo para sair da tendencia: ({ self.last_fast_gradient - correction_threshold:.3f})"
            )
            print(
                f'Gradiente rápido: {fast_gradient:.3f} ({ "Subindo" if fast_gradient > self.last_fast_gradient else "Descendo" })'
            )
            print(
                f'Gradiente lento: {slow_gradient:.3f} ({ "Subindo" if slow_gradient > self.last_slow_gradient else "Descendo" })'
            )
            print(
                f"  -Porcentagem de crescimento do gradiente rápido: (\033[1m{self.percentage_fromUP_fast_gradient:.3f}%)\033[0m\n"
                f"  -Porcentagem de Decremento do gradiente rápdido: (\033[1m{self.percentage_fromDOWN_fast_gradient:.3f}%)\033[0m\n"
            )
            print("\n📊 Indicador MACD:")
            print(f"MACD: {macd_values['MACD']:.5f}")
            print(f"Linha de Sinal: {macd_values['Signal']:.5f}")
            print(f"Histograma: {macd_values['Histograma']:.5f}")
            print(
                f"taxa de crescimento do histograma do MACD : {macd_histogram_rate_of_change:.3f}%"
            )
            print(f"Sinal de Compra: {macd_values['Buy_Signal']}")
            print(f"Sinal de Venda: {macd_values['Sell_Signal']}\n")
            if ma_trade_decision is None:
                print("Decisao do bot: Manter Posição")
            else:
                print(f"Decisao do bot: {'Comprar' if ma_trade_decision else 'Vender'}")
            print("\n---------------")

            message = (
                f"{'\n---------------'}\n"
                f"Estratégia executada: Moving Average com Volatilidade + Gradiente\n"
                f"{self.operation_code}:\n"
                f"{last_ma_fast:.3f} - Ultima Media Rapida \n{last_ma_slow:.3f} - Ultima Media Lenta\n"
                f"Ultima Volatilidade: {last_volatility:.3f}\n"
                f"Media da Volatilidade: {volatility:.3f}\n"
                f"Diferenca Atual: {current_difference:.3f}\n"
                f"Ultimo RSI: {last_rsi:.3f}\n"
                f"^indicador de tendencia de alta:\n"
                f"  - Media recente dos Gradientes rapidos: {self.recent_average:.3f}\n"
                f"  - Media necessaria para tendecia de alta: {growth_threshold * prev_ma_fast:.3f}\n"
                f"  - gradiente rapido maximo para sair da tendencia: ({ self.last_fast_gradient - correction_threshold:.3f})\n"
                f'Gradiente rápido: {fast_gradient:.3f} ({ "Subindo" if fast_gradient > self.last_fast_gradient else "Descendo" })\n'
                f'Gradiente lento: {slow_gradient:.3f} ({ "Subindo" if slow_gradient > self.last_slow_gradient else "Descendo" })\n'
                f"  -Porcentagem de crescimento do gradiente rapido: {self.percentage_fromUP_fast_gradient:.3f}%\n"
                f"  -Porcentagem de Decremento do gradiente rapdido: {self.percentage_fromDOWN_fast_gradient:.3f}%\n"
                f"\n📊 Indicador MACD:\n"
                f"MACD: {macd_values['MACD']:.5f}\n"
                f"Linha de Sinal: {macd_values['Signal']:.5f}\n"
                f"Histograma: {macd_values['Histograma']:.5f}\n"
                f"taxa de crescimento do histograma do MACD : {macd_histogram_rate_of_change:.3f}%"
                f"Sinal de Compra: {macd_values['Buy_Signal']}\n"
                f"Sinal de Venda: {macd_values['Sell_Signal']}\n"
                f'Decisao do bot: {"Comprar" if ma_trade_decision == True else "Vender"}\n'
                f"{'\n---------------'}\n"
            )
            bot_logger.info(message)

            dados_from_gemini = (
                f'posição atual do ativo: {"Comprado" if self.actual_trade_position == True else "Vendido"}\n'
                f"{self.operation_code}:\n"
                f"{last_ma_fast:.3f} - Ultima Media Rapida \n{last_ma_slow:.3f} - Ultima Media Lenta\n"
                f"Ultima Volatilidade: {last_volatility:.3f}\n"
                f"Media da Volatilidade: {volatility:.3f}\n"
                f"Diferenca Atual: {current_difference:.3f}\n"
                f"Ultimo RSI: {last_rsi:.3f}\n"
                f"^indicador de tendencia de alta:\n"
                f"  - Media recente dos Gradientes rapidos: {self.recent_average:.3f}\n"
                f"  - Media necessaria para tendecia de alta: {growth_threshold * prev_ma_fast:.3f}\n"
                f"  - gradiente rapido maximo para sair da tendencia: ({ self.last_fast_gradient - correction_threshold:.3f})\n"
                f'Gradiente rápido: {fast_gradient:.3f} ({ "Subindo" if fast_gradient > self.last_fast_gradient else "Descendo" })\n'
                f'Gradiente lento: {slow_gradient:.3f} ({ "Subindo" if slow_gradient > self.last_slow_gradient else "Descendo" })\n'
                f"  -Porcentagem de crescimento do gradiente rapido: {self.percentage_fromUP_fast_gradient:.3f}%\n"
                f"  -Porcentagem de Decremento do gradiente rapdido: {self.percentage_fromDOWN_fast_gradient:.3f}%\n"
                f"\n📊 Indicador MACD:\n"
                f"MACD: {macd_values['MACD']:.5f}\n"
                f"Linha de Sinal: {macd_values['Signal']:.5f}\n"
                f"Histograma: {macd_values['Histograma']:.5f}\n"
                f"taxa de crescimento do histograma do MACD : {macd_histogram_rate_of_change:.3f}%"
                f"Sinal de Compra: {macd_values['Buy_Signal']}\n"
                f"Sinal de Venda: {macd_values['Sell_Signal']}\n"
            )

            # Dados extraídos da mensagem
            dados = {
                "Posição Atual do Ativo": [
                    "Comprado" if self.actual_trade_position == True else "Vendido"
                ],
                "Código da Operação": [self.operation_code],
                "Última Média Rápida": [round(last_ma_fast, 3)],
                "Última Média Lenta": [round(last_ma_slow, 3)],
                "Última Volatilidade": [round(last_volatility, 3)],
                "Média da Volatilidade": [round(volatility, 3)],
                "Diferença Atual": [round(current_difference, 3)],
                "Último RSI": [round(last_rsi, 3)],
                "Média Recente dos Gradientes Rápidos": [round(self.recent_average, 3)],
                "Média Necessária para Tendência de Alta": [
                    round(growth_threshold * prev_ma_fast, 3)
                ],
                "Gradiente Rápido Máximo para Sair da Tendência": [
                    round(self.last_fast_gradient - correction_threshold, 3)
                ],
                "Gradiente Rápido": [round(fast_gradient, 3)],
                "Direção do Gradiente Rápido": [
                    "Subindo" if fast_gradient > self.last_fast_gradient else "Descendo"
                ],
                "Gradiente Lento": [round(slow_gradient, 3)],
                "Direção do Gradiente Lento": [
                    "Subindo" if slow_gradient > self.last_slow_gradient else "Descendo"
                ],
                "Porcentagem de Crescimento do Gradiente Rápido": [
                    round(self.percentage_fromUP_fast_gradient, 3)
                ],
                "Porcentagem de Decremento do Gradiente Rápido": [
                    round(self.percentage_fromDOWN_fast_gradient, 3)
                ],
                "MACD": [round(macd_values["MACD"], 5)],
                "Linha de Sinal": [round(macd_values["Signal"], 5)],
                "Histograma do MACD": [round(macd_values["Histograma"], 5)],
                "Taxa de Crescimento do Histograma do MACD": [
                    round(macd_histogram_rate_of_change, 3)
                ],
                "Sinal de Compra": [macd_values["Buy_Signal"]],
                "Sinal de Venda": [macd_values["Sell_Signal"]],
            }

            # Criando o DataFrame com os dados
            analise_bot = pd.DataFrame(dados)

            try:
                data_coletor = DataCollector(min_data_size=10)
                data_coletor.add_data(analise_bot)
                if data_coletor.check_data_availability() == True:
                    df = data_coletor.get_data()

                    result(df)
            except Exception as e:
                message = f"Erro ao executar a coleta de dados : {str(e)}"
                print(message)
                erro_logger.error(message)

            try:
                gemini = GeminiTradingBot(dados_from_gemini)
                decision, decision_bool = gemini.geminiTrader()

                if (
                    ma_trade_decision == True
                    and decision_bool == False
                    or ma_trade_decision is None
                    and decision_bool == False
                ):
                    ma_trade_decision = False
                    print(
                        f"\n -- Bot decidiu Comprar mais Gemini achou mais sensato vender --\n"
                    )
                    message = f"\n -- Bot decidiu Comprar mais Gemini achou mais sensato vender --\n"
                    bot_logger.info(message)

                elif (
                    ma_trade_decision == False
                    and decision_bool == True
                    or ma_trade_decision is None
                    and decision_bool == True
                ):
                    ma_trade_decision = True
                    print(
                        f"\n -- Bot decidiu Vender mais Gemini achou mais sensato comprar --\n"
                    )
                    message = f"\n -- Bot decidiu Vender mais Gemini achou mais sensato comprar --\n"
                    bot_logger.info(message)

            except Exception as e:
                message = f"Erro ao executar a estratégia : {str(e)}"
                print(message)
                erro_logger.error(message)

            print(decision)
            bot_logger.info(decision)

            if ma_trade_decision is None:
                message = f"\n -- Decisão Final manter Posição --\n"
            else:
                message = (
                    f"Decisao do bot: {'Comprar' if ma_trade_decision else 'Vender'}"
                )
            print(message)
            bot_logger.info(message)

        except IndexError:
            message(
                "Erro: Dados insuficientes para calcular a estratégia Moving Average Vergence."
            )
            erro_logger.error(message)
            return False

        return ma_trade_decision
