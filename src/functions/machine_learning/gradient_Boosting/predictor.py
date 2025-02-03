import logging
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.metrics import accuracy_score
from tqdm import tqdm

from functions.machine_learning.gradient_Boosting import (
    feature_engineering,
    model_evaluation,
    model_training,
)


class Predictor:
    def __init__(self, data, model_class, params=None):
        """
        Inicializa o preditor com os dados e o modelo.

        Parâmetros:
        - data: Dados para treino e teste.
        - model_class: Classe do modelo a ser treinado.
        - params: Parâmetros adicionais para o modelo (se houver).
        """
        self.data = data
        self.model_class = model_class
        self.params = params or {}

        # Divisão de dados (80% treino, 20% teste)
        self.X_train, self.X_test, self.y_train, self.y_test = self._split_data()
        self.model = None
        self.feature_engineer = feature_engineering(self.X_train, self.y_train)
        self.model_trainer = model_training(
            self.model_class, self.X_train, self.y_train, self.params
        )
        self.model_evaluator = model_evaluation.ModelEvaluation(
            self.model, self.X_test, self.y_test
        )

    def _split_data(self):
        """
        Divide os dados em conjuntos de treino e teste.

        Retorna:
        - X_train: Features de treino.
        - X_test: Features de teste.
        - y_train: Labels de treino.
        - y_test: Labels de teste.
        """
        # Verificação de dados
        if "target" not in self.data.columns:
            raise ValueError("Coluna 'target' não encontrada nos dados")

        X = self.data.drop(columns=["target"])
        y = self.data["target"]
        return train_test_split(X, y, test_size=0.2, random_state=42)

    def preprocess_data(self):
        """
        Aplica o pré-processamento e engenharia de características nos dados de treino e teste.
        """
        self.X_train, self.y_train = self.feature_engineer.create_features(
            self.X_train, self.y_train
        )
        self.X_test, self.y_test = self.feature_engineer.create_features(
            self.X_test, self.y_test
        )

    def train_model(self, use_grid_search=False):
        """
        Treina o modelo usando os dados processados.

        Parâmetro:
        - use_grid_search: Se True, aplica GridSearchCV para ajuste de hiperparâmetros.
        """
        if use_grid_search:
            logging.info("Iniciando GridSearch para ajuste de hiperparâmetros...")
            # Adicionando a barra de progresso para GridSearchCV
            grid_search = GridSearchCV(self.model_class(), self.params, cv=5, n_jobs=-1)

            # Envolvendo o GridSearchCV em um loop de tqdm
            grid_search.fit(tqdm(self.X_train, desc="Treinando Modelo com GridSearch"))

            self.model = grid_search
            logging.info(f"Melhores parâmetros encontrados: {grid_search.best_params_}")
        else:
            self.model = self.model_trainer.train_model()

    def evaluate_model(self):
        """
        Avalia o modelo treinado utilizando métricas de desempenho.
        """
        self.model_evaluator = model_evaluation(self.model, self.X_test, self.y_test)
        metrics = self.model_evaluator.evaluate()
        logging.info(f"Métricas de avaliação: {metrics}")
        return metrics

    def plot_evaluation_metrics(self):
        """
        Plota as métricas de avaliação do modelo.
        """
        self.model_evaluator.plot_confusion_matrix(["Classe 0", "Classe 1"])
        self.model_evaluator.plot_roc_curve()
        self.model_evaluator.plot_precision_recall_curve()
        self.model_evaluator.plot_precision_vs_threshold()

    def predict(self, new_data):
        """
        Faz previsões com o modelo treinado.

        Parâmetros:
        - new_data: Dados para previsão.

        Retorna:
        - predictions: Previsões do modelo.
        """
        if self.model is None:
            raise ValueError(
                "Modelo não treinado. Execute 'train_model' antes de prever."
            )

        new_data = self.feature_engineer.transform(new_data)
        predictions = self.model.predict(new_data)
        return predictions

    def run(self, use_grid_search=False):
        """
        Executa o fluxo completo: pré-processamento, treino, avaliação e previsões.
        """
        logging.info("Iniciando o processo de predição...")

        # Pré-processamento de dados
        self.preprocess_data()

        # Treinamento do modelo
        self.train_model(use_grid_search)

        # Avaliação do modelo
        metrics = self.evaluate_model()

        # Plotando as métricas
        self.plot_evaluation_metrics()

        return self.model, metrics
