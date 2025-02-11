import os
import pandas as pd
from datetime import datetime, timedelta
from binance.client import Client
from estrategias.getMovingAverageVergenceRSI import getMovingAverageVergenceRSI
from functions.machine_learning.coletor_dados.dynamic_dataFrame_saver import (
    DynamicDataCollector,
)

api_key = os.getenv("BINANCE_API_KEY")
secret_key = os.getenv("BINANCE_SECRET_KEY")
OPERATION_CODE = "SOLUSDT"


class DadosHistoricosParaTreinamento:
    def __init__(self, simbolo, intervalo, inicio, fim):
        try:
            self.simbolo = simbolo
            self.intervalo = intervalo
            self.inicio = inicio
            self.fim = fim
            self.client_binance = Client(
                api_key, secret_key
            )  # Inicialize o cliente Binance aqui
            self.estrategia = (
                None  # Inicialize a estratégia aqui ou dentro de 'coletar_dados'
            )
            self.inicio = self.inicio.strftime("%Y-%m-%d %H:%M:%S")
            self.fim = self.fim.strftime("%Y-%m-%d %H:%M:%S")
        except Exception as e:
            print(f"Erro ao inicializar a classe DadosHistoricosParaTreinamento: {e}")
            return None

    def obter_dados_historicos(self):
        """Obtém dados históricos do gráfico dentro do intervalo especificado."""
        try:
            klines = self.client_binance.get_historical_klines(
                self.simbolo, self.intervalo, self.inicio, self.fim
            )
            df = pd.DataFrame(
                klines,
                columns=[
                    "timestamp",
                    "open",
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

            # Converta as colunas relevantes para o tipo numérico
            for col in ["open", "high_price", "low_price", "close_price", "volume"]:
                df[col] = pd.to_numeric(df[col])

            df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")

            return df
        except Exception as e:
            print(f"Erro ao obter dados históricos: {e}")
            return None

    def aplicar_estrategia(self, df, current_price_from_buy_order):
        """Aplica a estratégia a cada linha do DataFrame."""
        resultados = []
        for i in range(len(df)):
            # Pegue um pedaço do dataframe
            df_parte = df.iloc[: i + 1].copy()
            # print(df_parte)
            try:
                if (
                    self.estrategia is None
                ):  # Inicializa a estratégia se ainda não estiver
                    # Cria uma instância da classe `estrategies`
                    estrategias = getMovingAverageVergenceRSI(
                        stock_data=df_parte,
                        volume_threshold=1.5,
                        rsi_period=5,
                        rsi_upper=70,
                        rsi_lower=30,
                        stop_loss=0.05,
                        stop_gain=0.10,
                        operation_code=OPERATION_CODE,  # Passa o código da operação
                        current_price_from_buy_order=current_price_from_buy_order,
                    )

                dados_estrategia = estrategias.getMovingAverageVergenceRSI(
                    fast_window=7,
                    slow_window=40,
                    volatility_factor=0.3,
                    initial_purchase_price=0,
                )

                # Salva os indicadores em um dicionário
                dados_estrategia = {
                    "Preço de Abertura": self.estrategia.current_price,
                    "Código da Operação": [self.operation_code],
                    "Preço de Abertura": [round(self.current_price, 3)],
                    "Maxima Alta": [round(self.max_high, 3)],
                    "Minima Baixa": [round(self.min_low, 3)],
                    "Preço de Fechamento": [round(self.estrategia.closing_price, 3)],
                    "Última Média Rápida": [round(self.estrategia.last_ma_fast, 3)],
                    "Última Média Lenta": [round(self.estrategia.last_ma_slow, 3)],
                    "Última Volatilidade": [round(self.estrategia.last_volatility, 3)],
                    "Média da Volatilidade": [round(self.estrategia.volatility, 3)],
                    "Diferença Atual": [round(self.estrategia.current_difference, 3)],
                    "Último RSI": [round(self.estrategia.last_rsi, 3)],
                    "Média Recente dos Gradientes Rápidos": [
                        round(self.recent_average, 3)
                    ],
                    "Média Necessária para Tendência de Alta": [
                        round(
                            self.estrategia.growth_threshold
                            * self.estrategia.prev_ma_fast,
                            3,
                        )
                    ],
                    "Gradiente Rápido Máximo para Sair da Tendência": [
                        round(
                            self.last_fast_gradient
                            - self.estrategia.correction_threshold,
                            3,
                        )
                    ],
                    "Gradiente Rápido": [round(self.estrategia.fast_gradient, 3)],
                    "Direção do Gradiente Rápido": [
                        (
                            "Subindo"
                            if self.estrategia.fast_gradient > self.last_fast_gradient
                            else "Descendo"
                        )
                    ],
                    "Gradiente Lento": [round(self.estrategia.slow_gradient, 3)],
                    "Direção do Gradiente Lento": [
                        (
                            "Subindo"
                            if self.estrategia.slow_gradient > self.last_slow_gradient
                            else "Descendo"
                        )
                    ],
                    "Porcentagem de Crescimento do Gradiente Rápido": [
                        round(self.percentage_fromUP_fast_gradient, 3)
                    ],
                    "Porcentagem de Decremento do Gradiente Rápido": [
                        round(self.percentage_fromDOWN_fast_gradient, 3)
                    ],
                    "MACD": [round(self.estrategia.macd_values["MACD"], 5)],
                    "Linha de Sinal": [round(self.estrategia.macd_values["Signal"], 5)],
                    "Histograma do MACD": [
                        round(self.estrategia.macd_values["Histograma"], 5)
                    ],
                    "Taxa de Crescimento do Histograma do MACD": [
                        round(self.estrategia.macd_histogram_rate_of_change, 3)
                    ],
                    "Sinal de Compra": [self.estrategia.macd_values["Buy_Signal"]],
                    "Sinal de Venda": [self.estrategia.macd_values["Sell_Signal"]],
                    "Indicador Vortex +VI": [round(self.estrategia.Vortex_Maxima, 5)],
                    "Indicador Vortex -VI": [round(self.estrategia.Vortex_Minima, 5)],
                    "Taxa de Crescimento do +VI": [
                        round(self.estrategia.vortex_rate_of_change, 3)
                    ],
                }

                resultados.append(dados_estrategia)

            except Exception as e:
                print(f"Erro ao aplicar estratégia na linha {i}: {e}")

        return pd.DataFrame(resultados)

    def salvar_dados_treinamento(self, df):
        """Salva os dados treinamento em um arquivo CSV."""
        try:
            dataColetor = DynamicDataCollector(
                file_name="training_data", min_data_size=0
            )
            dataColetor.add_data(df)
        except Exception as e:
            print(f"Erro ao salvar dados treinamento: {e}")
