from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import GradientBoostingClassifier
import pandas as pd
import numpy as np


class ModelTraining:
    def __init__(self, df, target_column="Sinal de Compra"):
        """
        Inicializa o objeto com os dados e o nome da coluna target.
        """
        try:
            # Verificações de dados
            if df is None or len(df) == 0:
                raise ValueError("DataFrame vazio ou nulo")

            if target_column not in df.columns:
                raise ValueError(
                    f"A coluna target '{target_column}' não foi encontrada"
                )

            # Remover linhas duplicadas
            df = df.drop_duplicates()

            # Filtrar apenas linhas com valores não nulos na coluna target
            df = df.dropna(subset=[target_column])
            self.df = df
            self.target_column = target_column
            self.scaler = None
            self.X_train, self.X_test, self.y_train, self.y_test = (
                None,
                None,
                None,
                None,
            )
        except Exception as e:
            print(f"Erro ao inicializar o objeto: {str(e)}")
        except ValueError as ve:
            print("Erro:", str(ve))
        except TypeError as te:
            print("Erro:", str(te))

    def preprocess_data(self):
        """
        Preprocessa os dados para treinamento.
        """
        try:
            # Garantir que os dados estejam no formato correto
            self.df = self.df.copy()

            # Converter colunas numéricas
            self.df = self.df.apply(pd.to_numeric, errors="coerce")

            # Remover valores NaN que possam ter surgido
            self.df.dropna(inplace=True)

            # Definir X (features) e y (target)
            X = self.df.drop(columns=[self.target_column])
            y = self.df[self.target_column]

            # Verificar distribuição das classes
            unique_classes = y.value_counts()

            # Garantir que o target tenha pelo menos duas classes
            if len(unique_classes) < 2:
                raise ValueError(
                    "Erro: Target contém apenas uma classe. Não é possível treinar o modelo."
                )

            # Divisão dos dados em treino e teste
            self.X_train, self.X_test, self.y_train, self.y_test = train_test_split(
                X, y, test_size=0.2, stratify=y, random_state=42
            )

            # Selecionar apenas colunas numéricas para normalização
            num_cols = X.select_dtypes(include=["float64", "int64"]).columns.tolist()

            # Verificar se há colunas numéricas
            if not num_cols:
                raise ValueError(
                    "Erro: Nenhuma coluna numérica encontrada para normalização."
                )

            self.scaler = StandardScaler()
            self.X_train[num_cols] = self.scaler.fit_transform(self.X_train[num_cols])
            self.X_test[num_cols] = self.scaler.transform(self.X_test[num_cols])
        except Exception as e:
            print(f"Erro ao preprocessar os dados: {str(e)}")
        except ValueError as ve:
            print("Erro:", str(ve))
        except TypeError as te:
            print("Erro:", str(te))

    def train_model(self):
        """
        Treina o modelo de Gradient Boosting com tratamento para poucos dados.
        """
        try:
            # Se menos de 10 registros, duplicar dados
            if len(self.df) < 10:
                # Criar cópias do DataFrame original
                duplicated_dfs = [self.df.copy() for _ in range(10 // len(self.df) + 1)]
                augmented_df = pd.concat(duplicated_dfs, ignore_index=True)

                # Truncar para 10 linhas
                augmented_df = augmented_df.head(10)

                # Substituir o DataFrame original
                self.df = augmented_df

            # Preprocessar dados
            X = self.df.drop(columns=[self.target_column])
            y = self.df[self.target_column]

            # Divisão dos dados
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, stratify=y, random_state=42
            )

            # Selecionar colunas numéricas
            num_cols = X.select_dtypes(include=["float64", "int64"]).columns

            # Escalar features
            scaler = StandardScaler()
            X_train[num_cols] = scaler.fit_transform(X_train[num_cols])
            X_test[num_cols] = scaler.transform(X_test[num_cols])

            # Treinar modelo
            model = GradientBoostingClassifier(random_state=42)

            # Se muito poucos dados, usar menos divisões no GridSearchCV
            param_grid = {
                "n_estimators": [50, 100],
                "learning_rate": [0.1],
                "max_depth": [3, 5],
                "subsample": [0.8, 1.0],
            }

            grid_search = GridSearchCV(
                estimator=model,
                param_grid=param_grid,
                cv=min(3, len(X_train)),  # Reduzir divisões se poucos dados
                scoring="accuracy",
                n_jobs=-1,
            )

            grid_search.fit(X_train, y_train)

            self.model = grid_search.best_estimator_
            print(f"Melhores parâmetros: {grid_search.best_params_}")
            return self.model

        except Exception as e:
            print(f"Erro ao treinar o modelo: {str(e)}")
        except ValueError as ve:
            print("Erro:", str(ve))
        except TypeError as te:
            print("Erro:", str(te))
