# data_processing.py
import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler, StandardScaler
import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


class DataProcessor:
    def __init__(self, use_standard_scaler=False):
        self.use_standard_scaler = use_standard_scaler
        self.scaler = None
        self.scaler_fitted = False  # Para evitar data leakage

    def process_raw_data(self, df, horizonte=1):
        """
        Processa dados brutos SEM aplicar scaling (para evitar data leakage).
        Retorna o DataFrame com features e target.
        """
        try:
            # Converter para numérico e tratar NaNs
            df = df.apply(pd.to_numeric, errors="coerce")
            df = df.ffill().bfill()

            # Calcular features (sem dados futuros!)
            df["retorno"] = np.log(df["Preço de Fechamento"] / df["Preço de Abertura"])

            # Usar shift(horizonte) em vez de shift(-horizonte) para evitar dados futuros
            # Calcular variação percentual do preço (sem dados futuros)
            df["variacao_preco"] = (
                (
                    df["Preço de Fechamento"].shift(-horizonte)
                    - df["Preço de Fechamento"]
                )
                / df["Preço de Fechamento"]
                * 100
            )

            # Janela móvel adaptativa (máximo 10 períodos para datasets pequenos)
            window_size = min(10, len(df) - 1)  # Reduz a janela para 10 períodos
            if window_size < 1:
                raise ValueError("Dataset muito pequeno para gerar target.")

            df["target"] = 0  # Inicializa o target

            for i in range(window_size, len(df)):
                window_data = df["variacao_preco"].iloc[i - window_size : i]
                limiar_superior = window_data.quantile(0.75)
                limiar_inferior = window_data.quantile(0.25)
                current_value = df["variacao_preco"].iloc[i]

                if current_value > limiar_superior:
                    df.loc[df.index[i], "target"] = 1
                elif current_value < limiar_inferior:
                    df.loc[df.index[i], "target"] = -1

            # Verificar se há pelo menos duas classes
            target_counts = df["target"].value_counts()
            if len(target_counts) < 2:
                raise ValueError(
                    f"Erro: Target tem apenas {len(target_counts)} classe(s). "
                    "Aumente a variabilidade dos dados ou reduza a janela móvel."
                )

            return df

        except Exception as e:
            logging.error(f"Erro ao criar o target: {e}")
            raise ValueError(f"Falha no processamento: {e}") from e

    def fit_scaler(self, df):
        """Treina o scaler apenas nos dados de treino."""
        columns_to_scale = [
            "Última Média Rápida",
            "Última Média Lenta",
            ...,
        ]  # Suas colunas
        self.scaler = StandardScaler() if self.use_standard_scaler else MinMaxScaler()
        self.scaler.fit(df[columns_to_scale])
        self.scaler_fitted = True

    def transform_data(self, df):
        """Aplica o scaler treinado (usar após split treino/teste)."""
        if not self.scaler_fitted:
            raise ValueError("Scaler não treinado. Chame fit_scaler primeiro.")
        columns_to_scale = ["Última Média Rápida", "Última Média Lenta", ...]
        df[columns_to_scale] = self.scaler.transform(df[columns_to_scale])
        return df
