# model_training.py
from sklearn.model_selection import train_test_split, TimeSeriesSplit, GridSearchCV
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
import pandas as pd
import logging

logging.basicConfig(level=logging.INFO)


class ModelTraining:
    def __init__(self, df, target_column="target"):
        if df.empty:
            raise ValueError("DataFrame vazio.")
        self.df = df.dropna(subset=[target_column])
        self.target_column = target_column
        self.scaler = None
        self.model = None

    def preprocess_data(self):
        """Dividir dados antes de escalar!"""
        X = self.df.drop(columns=[self.target_column])
        y = self.df[self.target_column]

        # Verificar se há pelo menos duas classes
        if len(y.unique()) < 2:
            raise ValueError(
                "Erro: O target contém apenas uma classe. Verifique os dados."
            )

        # Split estratificado (preserva a proporção das classes)
        self.X_train, self.X_test, self.y_train, self.y_test = train_test_split(
            X, y, test_size=0.2, stratify=y, random_state=42
        )

        # Logs para depuração
        print("\n💡 Distribuição do target no treino:")
        print(self.y_train.value_counts())
        print("\n💡 Distribuição do target no teste:")
        print(self.y_test.value_counts())

        # Escalar APENAS com dados de treino
        numeric_cols = X.select_dtypes(include=["number"]).columns
        self.scaler = StandardScaler()
        self.X_train.loc[:, numeric_cols] = self.scaler.fit_transform(
            self.X_train[numeric_cols]
        )
        self.X_test.loc[:, numeric_cols] = self.scaler.transform(
            self.X_test[numeric_cols]
        )

    def train_model(self):
        """Treinar com validação cruzada temporal."""
        # Verificar se há dados suficientes
        if len(self.X_train) < 10:
            raise ValueError(
                "Erro: Conjunto de treino muito pequeno. Colete mais dados."
            )

        # Configurar GridSearchCV com menos combinações
        param_grid = {
            "n_estimators": [50],  # Reduzir o número de opções
            "max_depth": [3],
            "learning_rate": [0.1],
        }

        # Usar TimeSeriesSplit com menos divisões
        tscv = TimeSeriesSplit(n_splits=min(3, len(self.X_train)))

        grid_search = GridSearchCV(
            GradientBoostingClassifier(random_state=42),
            param_grid,
            cv=tscv,
            scoring="accuracy",
            n_jobs=-1,
            error_score="raise",  # Para debugar erros
        )

        grid_search.fit(self.X_train, self.y_train)
        self.model = grid_search.best_estimator_
        logging.info(f"Melhores parâmetros: {grid_search.best_params_}")
        return self.model
