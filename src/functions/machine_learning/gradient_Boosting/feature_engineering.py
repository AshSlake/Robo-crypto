import traceback
import pandas as pd
import numpy as np
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.utils import compute_sample_weight  # Importar a função correta


class FeatureEngineering:
    def __init__(self, df):
        pass
        self.df = df

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

        # 1. Variação percentual entre médias móveis (com tratamento de divisão por zero)
        df["var_perc_media"] = self.safe_divide(
            df["Última Média Rápida"] - df["Última Média Lenta"],
            df["Última Média Lenta"],
        )

        # 2. Diferença entre +VI e -VI do Vortex
        df["vortex_diferenca"] = df["Indicador Vortex +VI"] - df["Indicador Vortex -VI"]

        # 3. MACD Normalizado (com tratamento de divisão por zero)
        df["macd_normalizado"] = self.safe_divide(
            df["MACD"], df["Média da Volatilidade"] + df["Última Volatilidade"]
        )

        # 4. Suavização de indicadores com Exponential Moving Average (EMA)
        df["rsi_suave"] = df["Último RSI"].ewm(span=5).mean()
        df["macd_suave"] = df["MACD"].ewm(span=5).mean()
        df["linha_sinal_suave"] = df["Linha de Sinal"].ewm(span=5).mean()

        # 5.  Médias Móveis dos gradientes (se ainda forem usadas)
        if (
            "Gradiente Rápido" in df.columns and "Gradiente Lento" in df.columns
        ):  # Verifica se as colunas existem
            df["gradiente_rapido_suave"] = (
                df["Gradiente Rápido"].rolling(window=10).mean()
            )
            df["gradiente_lento_suave"] = (
                df["Gradiente Lento"].rolling(window=10).mean()
            )

        # 6. Indicador de Reversão (usando médias suavizadas)
        if (
            "gradiente_rapido_suave" in df.columns
            and "gradiente_lento_suave" in df.columns
        ):  # Verifica se as colunas existem
            df["indicador_reversao"] = np.where(
                (df["gradiente_rapido_suave"] < 0) & (df["gradiente_lento_suave"] > 0),
                1,
                0,
            )

        # 7. Força da Tendência (considerando outros indicadores)
        df["forca_tendencia"] = (
            (df["MACD"] > df["Linha de Sinal"]).astype(int)
            + (df["Indicador Vortex +VI"] > df["Indicador Vortex -VI"]).astype(int)
            + (df["Último RSI"] > 50).astype(
                int
            )  # RSI acima de 50 sugere tendência de alta
        )

        # Remover colunas irrelevantes ou redundantes (incluindo as originais se as transformadas forem usadas)
        columns_to_drop = [
            "Gradiente Rápido",
            "Gradiente Lento",
            "Média Recente dos Gradientes Rápidos",  # Remova se não estiver sendo usada
            "Média Necessária para Tendência de Alta",  # Remova se não estiver sendo usada
            "Gradiente Rápido Máximo para Sair da Tendência",  # Remova se não estiver sendo usada
            # Adicione outras colunas irrelevantes aqui
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

    def safe_divide(self, numerator, denominator):
        """Função auxiliar para evitar divisão por zero."""
        return np.where(denominator != 0, numerator / denominator, 0)
