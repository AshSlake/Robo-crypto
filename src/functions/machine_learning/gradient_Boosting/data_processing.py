import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler, StandardScaler


class DataProcessor:
    def __init__(self, use_standard_scaler=False):
        """
        Inicializa o processador de dados.
        - use_standard_scaler: Se True, usa StandardScaler ao invés de MinMaxScaler.
        """
        self.scaler = StandardScaler() if use_standard_scaler else MinMaxScaler()

    def process_raw_data(self, df):
        """
        Processa um DataFrame com dados brutos e retorna um DataFrame pronto para Machine Learning.
        """

        # Tratamento de dados: Converter tudo para float, removendo strings e erros
        for col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

        # Preencher valores NaN com a média da coluna (ou outro valor adequado)
        df.fillna(df.mean(), inplace=True)

        # Criar novas features
        df["gradiente_rapido_crescimento"] = (
            df["Porcentagem de Crescimento do Gradiente Rápido"] / 100
        )
        df["gradiente_rapido_decremento"] = (
            df["Porcentagem de Decremento do Gradiente Rápido"] / 100
        )
        df["macd_diferenca"] = df["MACD"] - df["Linha de Sinal"]
        df["histograma_variação"] = (
            df["Histograma do MACD"] - df["Taxa de Crescimento do Histograma do MACD"]
        )

        # Criar uma feature de tendência baseada nos gradientes
        df["tendencia_alta"] = np.where(
            (
                df["Média Recente dos Gradientes Rápidos"]
                > df["Média Necessária para Tendência de Alta"]
            )
            & (
                df["Gradiente Rápido"]
                > df["Gradiente Rápido Máximo para Sair da Tendência"]
            ),
            1,
            0,
        )

        # Criar relação entre gradiente rápido e lento
        df["relacao_gradientes"] = df["Gradiente Rápido"] / (
            df["Gradiente Lento"] + 1e-6
        )

        # Escolher colunas para normalização
        columns_to_scale = [
            "Última Média Rápida",
            "Última Média Lenta",
            "Última Volatilidade",
            "Média da Volatilidade",
            "Diferença Atual",
            "Último RSI",
            "MACD",
            "Linha de Sinal",
            "Histograma do MACD",
        ]

        df[columns_to_scale] = self.scaler.fit_transform(df[columns_to_scale])

        # Criar rótulo de compra/venda baseado na próxima variação de preço
        df["target"] = np.where(
            df["Sinal de Compra"], 1, np.where(df["Sinal de Venda"], -1, 0)
        )

        return df


# Exemplo de uso:
# processor = DataProcessor(use_standard_scaler=True)  # Alternar entre MinMax e StandardScaler
# df = processor.process_raw_data(dataframe_com_dados)
