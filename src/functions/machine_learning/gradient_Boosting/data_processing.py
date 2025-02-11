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

        # Criar tendência baseada em gradientes
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

        # Relação entre gradientes
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
            "retorno",
            "variacao_maxima",
            "variacao_minima",
        ]
        df[columns_to_scale] = self.scaler.fit_transform(df[columns_to_scale])

        # Substitua a seção de criação do target por algo como:
        df["target"] = 0
        window_size = 30  # Janela móvel de 30 períodos

        for i in range(len(df)):
            if i < window_size:
                continue
        # Limiares dinâmicos
        limiar_superior = df["variacao_preco"].iloc[i - window_size : i].quantile(0.75)
        limiar_inferior = df["variacao_preco"].iloc[i - window_size : i].quantile(0.25)

        if df["variacao_preco"].iloc[i] > limiar_superior:
            df["target"].iloc[i] = 1
        elif df["variacao_preco"].iloc[i] < limiar_inferior:
            df["target"].iloc[i] = -1

        # Condição de Compra (1)
        ma_50 = df["Preço de Fechamento"].rolling(window=50).mean()
        ma_200 = df["Preço de Fechamento"].rolling(window=200).mean()
        df.loc[
            (df["Último RSI"] < 30)  # RSI indica sobrevenda
            & (df["MACD"] > df["Linha de Sinal"])  # MACD cruza para cima
            & (df["Preço de Fechamento"] > ma_50)  # Preço acima da MA de 50 períodos
            & (df["variacao_preco"] > limiar_superior),  # Variação positiva forte
            "target",
        ] = 1

        # Condição de Venda (-1)
        df.loc[
            (df["Último RSI"] > 70)  # RSI indica sobrecompra
            & (df["MACD"] < df["Linha de Sinal"])  # MACD cruza para baixo
            & (df["Preço de Fechamento"] < ma_200)  # Preço abaixo da MA de 200 períodos
            & (df["variacao_preco"] < limiar_inferior),  # Variação negativa forte
            "target",
        ] = -1

        return df
