# feature_engineering.py
import pandas as pd
import numpy as np


class FeatureEngineering:
    def __init__(self, df):
        self.df = df.copy()

    def create_features(self):
        """Cria features usando apenas dados passados."""
        # Exemplo: Médias móveis com dados passados
        self.df["MA_50"] = (
            self.df["Preço de Fechamento"].rolling(window=50, min_periods=1).mean()
        )
        self.df["MA_200"] = (
            self.df["Preço de Fechamento"].rolling(window=200, min_periods=1).mean()
        )

        # Evitar divisão por zero
        self.df["relacao_volatilidade"] = np.where(
            self.df["Última Volatilidade"] != 0,
            self.df["Diferença Atual"] / self.df["Última Volatilidade"],
            0,
        )
        return self.df.dropna()  # Remover linhas com NaN geradas pelas médias móveis
