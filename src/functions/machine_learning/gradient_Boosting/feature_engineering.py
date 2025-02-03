import traceback
import pandas as pd
import numpy as np
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.utils import compute_sample_weight  # Importar a função correta


class FeatureEngineering:
    def __init__(self):
        pass

    def safe_divide(self, numerator, denominator):
        """
        Função para garantir a divisão segura, evitando divisões por zero.
        Retorna np.nan quando o denominador é zero.
        """
        return np.where(denominator != 0, numerator / denominator, np.nan)

    def clean_data(self, df):
        """
        Limpeza de dados: substitui valores ausentes por 0 e remove linhas com dados inválidos.
        """
        df.fillna(0, inplace=True)
        df.dropna(inplace=True)
        return df

    def create_features(self, df):
        """
        Cria novas features para melhorar a qualidade dos dados de entrada do modelo.
        """
        # 🔹 Variação percentual entre médias móveis
        df["var_perc_media_rapida"] = self.safe_divide(
            df["Última Média Rápida"] - df["Última Média Lenta"],
            df["Última Média Lenta"],
        )

        # 🔹 Normalização do MACD
        df["macd_normalizado"] = df["MACD"] / (
            df["Média da Volatilidade"] + df["Última Volatilidade"]
        )

        # 🔹 Suavização do gradiente rápido e lento
        df["gradiente_rapido_suave"] = df["Gradiente Rápido"].ewm(span=5).mean()
        df["gradiente_lento_suave"] = df["Gradiente Lento"].ewm(span=5).mean()

        # 🔹 Média simples de gradientes rápidos e lentos
        df["gradiente_rapido_suave_sma"] = (
            df["Gradiente Rápido"].rolling(window=10).mean()
        )
        df["gradiente_lento_suave_sma"] = (
            df["Gradiente Lento"].rolling(window=10).mean()
        )

        # 🔹 Criação de uma pontuação de tendência
        df["tendencia_score"] = (
            (
                df["Média Recente dos Gradientes Rápidos"]
                > df["Média Necessária para Tendência de Alta"]
            ).astype(int)
            + (df["gradiente_rapido_suave"] > df["gradiente_lento_suave"]).astype(int)
            + (df["macd_normalizado"] > 0).astype(int)
        )

        # 🔹 Transformação logarítmica para volatilidade
        df["log_volatilidade"] = np.log1p(df["Última Volatilidade"])

        # 🔹 Indicador de reversão
        df["indicador_reversao"] = np.where(
            (df["gradiente_rapido_suave"] < 0) & (df["gradiente_lento_suave"] > 0), 1, 0
        )

        # 🔹 Criar a coluna de target com base nos sinais de compra e venda
        df["column_target"] = df["target"].copy()

        # 🔹 Filtragem de colunas irrelevantes
        columns_to_drop = [
            "Gradiente Rápido",
            "Gradiente Lento",
            "Média Recente dos Gradientes Rápidos",
        ]
        df.drop(columns=columns_to_drop, inplace=True, errors="ignore")

        return df

    def evaluate_feature_importance(self, df, target_column):
        """
        Avalia a importância das features utilizando Gradient Boosting com tratamento de erros e balanceamento de classes.
        """
        try:  # Movendo o try para fora do loop para capturar erros de pré-processamento também
            X = df.drop(columns=[target_column])
            y = df[target_column]

            # Conversão de booleanos (aprimorada):
            for col in X.select_dtypes(
                include="object"
            ).columns:  # Iterar apenas em colunas de objeto
                try:  # Lidar com erros de conversão individualmente
                    X[col] = X[col].astype(bool).astype(int)  # Conversão mais direta
                except Exception as e:
                    print(f"Aviso: Erro ao converter coluna '{col}' para booleano: {e}")
                    # Lógica de fallback (manter como string, preencher com um valor, etc.)
                    X[col] = X[col].fillna(X[col].mode()[0])  # Preencher com a moda

            # Preenchimento de valores ausentes (aprimorado):
            for col in X.select_dtypes(
                include=np.number
            ).columns:  # Preencher apenas colunas numéricas
                if X[col].isnull().any():
                    X[col] = X[col].fillna(
                        X[col].median()
                    )  # Usar a mediana é mais robusto a outliers

            # Calcular pesos de classe (fora do try-except, se não for fonte de erro):

            sample_weights = compute_sample_weight("balanced", y=y)

            # Criar o modelo SEM class_weight:
            model = GradientBoostingClassifier(random_state=42)

            model.fit(X, y, sample_weight=sample_weights)

            importance = model.feature_importances_
            feature_importance = pd.DataFrame(
                {"Feature": X.columns, "Importance": importance}
            )
            feature_importance = feature_importance.sort_values(
                by="Importance", ascending=False
            )
            return feature_importance

        except Exception as e:
            print(f"Erro durante o cálculo da importância das features: {e}")
            traceback.print_exc()
            return pd.DataFrame({"Feature": [], "Importance": []})

    def generate_target(self, row):
        """
        Gera a variável alvo baseada nos sinais de compra e venda.

        Parâmetros:
            row (Series): Linha do DataFrame contendo os sinais de compra e venda.

        Retorna:
            int: 1 para compra, -1 para venda e 0 para neutro.
        """
        # Convertendo para booleano se necessário (caso estejam como string "True"/"False")
        sinal_compra = row["Sinal de Compra"]
        sinal_venda = row["Sinal de Venda"]

        if isinstance(sinal_compra, str):
            sinal_compra = sinal_compra.strip().lower() in ["true", "1", "yes"]
        if isinstance(sinal_venda, str):
            sinal_venda = sinal_venda.strip().lower() in ["true", "1", "yes"]

        if sinal_compra and not sinal_venda:
            return 1  # Compra
        elif sinal_venda and not sinal_compra:
            return -1  # Venda
        else:
            return 0  # Neutro
