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

        horizonte = 1
        # Calcular retornos logarítmicos dos preços (mais robusto que variação percentual simples)
        df["retorno"] = np.log(df["Preço de Fechamento"] / df["Preço de Abertura"])

        # Calcular a variação percentual entre o preço de fechamento e:
        df["variacao_maxima"] = (
            (df["Maxima Alta"] - df["Preço de Fechamento"])
            / df["Preço de Fechamento"]
            * 100
        )
        df["variacao_minima"] = (
            (df["Minima Baixa"] - df["Preço de Fechamento"])
            / df["Preço de Fechamento"]
            * 100
        )
        # Calcular a variação percentual do preço
        df["variacao_preco"] = (
            (df["Preço de Fechamento"].shift(-horizonte) - df["Preço de Fechamento"])
            / df["Preço de Fechamento"]
            * 100
        )

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
            "retorno",  # Nova coluna
            "variacao_maxima",  # Nova coluna
            "variacao_minima",  # Nova coluna
        ]

        df[columns_to_scale] = self.scaler.fit_transform(df[columns_to_scale])

        # Criar o alvo de classificação
        df["target"] = 0
        df.loc[df["variacao_preco"] > 0.5, "target"] = 1  # Comprar/Long (limiar menor)
        df.loc[df["variacao_preco"] < -0.5, "target"] = (
            -1
        )  # Vender/Short (limiar menor)

        return df


# Exemplo de uso:
# processor = DataProcessor(use_standard_scaler=True)  # Alternar entre MinMax e StandardScaler
# df = processor.process_raw_data(dataframe_com_dados)
