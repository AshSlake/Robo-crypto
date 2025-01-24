from http import client
import os

from werkzeug import Client
from db.neonDbConfig import (
    get_last_gradients_from_db,
    save_gradients_to_db_with_limit,
)

from functions.calculate_fast_gradients import calculate_fast_gradients
from functions.calculate_jump_threshold import calculate_jump_threshold
from functions.calculate_moving_average import calculate_moving_average
from functions.calculate_recent_growth_value import calculate_recent_growth_value
from functions.detect_new_price_jump import detect_new_price_jump
from functions.get_current_price import get_current_price
from functions.get_recent_prices import get_recent_prices
from functions.logger import erro_logger, bot_logger
from functions.RsiCalculationClass import TechnicalIndicators
from functions.CandlestickDataExtractor import CandlestickDataExtractor
from binance.client import Client

from functions.update_fast_gradients import update_fast_gradients

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
        # Variáveis adicionais
        self.last_fast_gradient = None
        self.last_slow_gradient = None
        self.prev_rsi = None
        self.client_binance = Client(api_key, secret_key)
        self.alerta_de_crescimento_rapido = False
        self.fast_gradients = []
        self.current_price = None
        self.interval = Client.KLINE_INTERVAL_15MINUTE
        self.recent_average = None
        self.state_after_correction = None

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
            stop_loss_price = initial_purchase_price * (1 - stop_loss_percentage)

            # Obter dados recentes de preços
            prices = get_recent_prices(
                self, symbol=self.operation_code, interval=self.interval, limit=500
            )

            # Exemplo de como calcular os fast_gradients na estratégia
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

            self.recent_average = calculate_recent_growth_value(
                self, fast_gradients, growth_threshold, prev_ma_fast
            )

            # CONDIÇÕES DE COMPRA
            if (
                current_difference > volatility * volatility_factor
                and last_volatility < volatility
                and self.rsi_lower < last_rsi < self.rsi_upper
            ):
                ma_trade_decision = True
                print(
                    "Compra: A diferença atual é maior que a volatilidade ajustada, indicando uma possível tendência de alta. "
                    "A volatilidade atual é menor que a média, sugerindo estabilidade no mercado, "
                    "e o RSI está dentro do intervalo desejado, sinalizando uma condição de compra favorável."
                )
                message = (
                    f"Compra: A diferença atual é maior que a volatilidade ajustada, indicando uma possível tendência de alta.\n "
                    f"A volatilidade atual é menor que a média, sugerindo estabilidade no mercado, \n"
                    f"e o RSI está dentro do intervalo desejado, sinalizando uma condição de compra favorável.\n"
                )
                bot_logger.info(message)

            elif (
                last_ma_fast > last_ma_slow + hysteresis
                and current_difference < volatility * volatility_factor
                and last_volatility > volatility
                and fast_gradient > slow_gradient
                and last_rsi > self.rsi_lower < self.rsi_upper
            ):
                ma_trade_decision = True  # Sinal de compra
                print(
                    "Compra: A MA rápida está acima da MA lenta ajustada por histerese, e a volatilidade anterior é significativa, \n"
                    "sugerindo um mercado dinâmico. O gradiente rápido maior que o lento e o RSI acima do limite inferior e abaixo do limite maximo reforçam uma perspectiva de compra.\n"
                )
                message = (
                    f"Compra: A MA rápida está acima da MA lenta ajustada por histerese, e a volatilidade anterior é significativa,\n "
                    f"sugerindo um mercado dinâmico. O gradiente rápido maior que o lento e o RSI acima do limite inferior reforçam uma perspectiva de compra.\n"
                )
                bot_logger.info(message)

            elif (
                last_ma_fast > last_ma_slow + hysteresis
                and last_volatility < volatility
                and last_rsi > self.rsi_lower
                and fast_gradient > (slow_gradient * 2)
            ):
                ma_trade_decision = True  # Sinal de compra
                print(
                    "Compra: A volatilidade anterior é maior que a atual, indicando possível consolidação do mercado.\n "
                    "O RSI acima do limite superior sugere forte momentum de compra, \n"
                    "e o gradiente rápido sendo significativamente maior que o lento confirma o forte impulso de alta.\n"
                )
                message = (
                    f"Compra: A volatilidade anterior é maior que a atual, indicando possível consolidação do mercado.\n "
                    f"O RSI acima do limite superior sugere forte momentum de compra, \n"
                    f"e o gradiente rápido sendo significativamente maior que o lento confirma o forte impulso de alta.\n"
                )
                bot_logger.info(message)

            # CONDIÇÕES DE VENDA
            # 1
            elif (
                last_ma_fast < last_ma_slow - hysteresis
                and self.alerta_de_crescimento_rapido == False
            ):
                ma_trade_decision = False  # Sinal de venda
                print(
                    "Venda: A MA rápida cruzou abaixo da MA lenta ajustada por histerese, sinalizando uma possível reversão de tendência para baixa.\n"
                )
                message = f"Venda: A MA rápida cruzou abaixo da MA lenta ajustada por histerese, sinalizando uma possível reversão de tendência para baixa.\n"
                bot_logger.info(message)
            # 2
            elif (
                last_ma_fast > last_ma_slow
                and last_volatility > volatility
                and fast_gradient < slow_gradient
                and last_rsi < self.rsi_lower
                and self.alerta_de_crescimento_rapido == False
            ):
                ma_trade_decision = False  # Sinal de venda
                print(
                    "Venda: Apesar da MA rápida estar acima da lenta, a alta volatilidade e o gradiente rápido menor que o lento \n"
                    "ou o RSI abaixo do limite inferior sugerem um risco de reversão. Melhor realizar vendas.\n"
                )
                message = (
                    f"Venda: Apesar da MA rápida estar acima da lenta, a alta volatilidade e o gradiente rápido menor que o lento \n"
                    f"ou o RSI abaixo do limite inferior sugerem um risco de reversão. Melhor realizar vendas.\n"
                )
                bot_logger.info(message)
            # 3
            elif (
                last_volatility > volatility
                and last_rsi < self.rsi_lower
                and self.alerta_de_crescimento_rapido == False
            ):
                ma_trade_decision = False
                print(
                    "Venda: A volatilidade anterior maior que a atual e o RSI abaixo do limite inferior\n "
                    "sugerem um enfraquecimento no mercado, indicando uma possível condição de venda.\n"
                )
                message = (
                    f"Venda: A volatilidade anterior maior que a atual e o RSI abaixo do limite inferior \n"
                    f"sugerem um enfraquecimento no mercado, indicando uma possível condição de venda.\n"
                )
                bot_logger.info(message)
            # 4
            elif (
                fast_gradient < self.last_fast_gradient - hysteresis
                and last_rsi < self.prev_rsi - hysteresis
                and last_rsi < self.rsi_lower + hysteresis
                and self.alerta_de_crescimento_rapido == False
            ):
                ma_trade_decision = False  # Sinal de venda
                print(
                    "Venda: O gradiente rápido diminuiu significativamente e o RSI abaixo do ultimo valor do RSI,\n e o RSI atual é menor que o minimo\n "
                    "indicando uma possível reversão de tendência para baixa.\n"
                )
                message = (
                    f"Venda: O gradiente rápido diminuiu significativamente e o RSI abaixo do ultimo valor do RSI, \n"
                    f"indicando uma possível reversão de tendência para baixa.\n"
                )
                bot_logger.info(message)

            # 5
            # Verificar se o preço atual caiu abaixo do stop-loss
            elif self.current_price < stop_loss_price:
                ma_trade_decision = False  # Sinal de venda devido ao stop-loss
                print(
                    f"\n ------------------ \nStop-Loss Ativado: O preço atual de {self.current_price:.3f} caiu abaixo do nível de stop-loss de {stop_loss_price:.2f}.\n "
                    "Realizando venda para limitar as perdas.\n ------------------ \n"
                )
                message = (
                    f"Stop-Loss Ativado: O preço atual de {self.current_price:.3f} caiu abaixo do nível de stop-loss de {stop_loss_price:.2f}. \n"
                    f"Realizando venda para limitar as perdas.\n"
                )
                bot_logger.info(message)

            # 6
            elif (
                last_volatility < volatility
                and last_rsi < self.rsi_lower + hysteresis
                and fast_gradient < 0
            ):
                print(
                    f"\n ------------------ \nCrescimento Rápido de baixa Detected: O gradiente rápido diminuiu significativamente, indicando uma forte tendência de baixa.\n ------------------ \n"
                )
                message = f"Crescimento Rápido de Baixa Detected: O gradiente rápido diminuiu significativamente, indicando uma forte tendência de baixa.\n"
                bot_logger.info(message)
                ma_trade_decision = False  # Sinal de venda
            # 7
            # Detectar crescimento rápido no gradiente rápido
            if self.recent_average > growth_threshold * prev_ma_fast:
                print(
                    f"\n ------------------ \n Crescimento Consistente Detectado: O gradiente médio recente aumentou significativamente, indicando uma forte tendência de alta.\n ------------------ \n"
                )
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

                    print(
                        f"\n ------------------ \nCorreção Detectada: O gradiente rápido começou a corrigir, caindo de {self.last_fast_gradient:.5f} para {fast_gradient:.3f},\n "
                        "indicando uma possível reversão ou ajuste no mercado.\n ------------------ \n"
                    )
                    message = (
                        f"Correção Detectada: O gradiente rápido começou a corrigir, caindo de {self.last_fast_gradient:.5f} para {fast_gradient:.3f},\n "
                        f"indicando uma possível reversão ou ajuste no mercado."
                    )
                    bot_logger.info(message)

                elif self.state_after_correction:
                    # Verificar se há uma continuação na alta
                    if detect_new_price_jump(
                        self, fast_gradient, prices, jump_threshold
                    ):
                        ma_trade_decision = True  # Confirmação de alta pós-correção
                        self.state_after_correction = False  # Resetar estado
                        print(
                            f"\n ------------------ \nContinuação da Alta Confirmada: O preço ou gradiente mostram um novo salto significativo, validando a retomada da alta.\n ------------------ \n"
                        )
                        bot_logger.info(
                            f"Continuação da Alta Confirmada: O preço ou gradiente mostram um novo salto significativo, validando a retomada da alta.\n"
                        )
                    else:
                        print(
                            "\n ------------------ \nEspera: Ainda não foi detectado um novo salto no preço ou gradiente. Continuar monitorando.\n ------------------ \n"
                        )
                        bot_logger.info(
                            f"Espera: Ainda não foi detectado um novo salto no preço ou gradiente. Continuar monitorando.\n"
                        )
            else:
                self.alerta_de_crescimento_rapido = False

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
            if ma_trade_decision is None:
                print("Decisao: Manter Posição")
            else:
                print(f"Decisao: {'Comprar' if ma_trade_decision else 'Vender'}")
            print("-----")

            message = (
                f"{'---------------'}\n"
                f"Estratégia executada: Moving Average com Volatilidade + Gradiente\n"
                f"{self.operation_code}:\n"
                f"{last_ma_fast:.3f} - Ultima Media Rapida \n{last_ma_slow:.3f} - Ultima Media Lenta\n"
                f"Ultima Volatilidade: {last_volatility:.3f}\n"
                f"Media da Volatilidade: {volatility:.3f}\n"
                f"Diferenca Atual: {current_difference:.3f}\n"
                f"Ultimo RSI: {last_rsi:.3f}\n"
                f"^indicador de tendencia de alta:\n  - gradiente rapido necessario ({growth_threshold * prev_ma_fast:.3f})\n"
                f"  - gradiente maximo para sair da tendencia: ({ self.last_fast_gradient - correction_threshold:.3f})\n"
                f'Gradiente rapido: {fast_gradient:.3f} ({ "Subindo" if fast_gradient > self.last_fast_gradient else "Descendo" })\n'
                f'Gradiente lento: {slow_gradient:.3f} ({ "Subindo" if slow_gradient > self.last_slow_gradient else "Descendo" })\n'
                f'Decisao: {"Comprar" if ma_trade_decision == True else "Vender"}\n'
                f"{'---------------'}\n"
            )
            bot_logger.info(message)

        except IndexError:
            message(
                "Erro: Dados insuficientes para calcular a estratégia Moving Average Vergence."
            )
            erro_logger.error(message)
            return False

        return ma_trade_decision
