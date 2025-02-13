# result.py
import numpy as np
import pandas as pd
from functions.machine_learning.gradient_BoostingV2.DataProcessor import DataProcessor
from functions.machine_learning.gradient_BoostingV2.FeatureEngineering import (
    FeatureEngineering,
)
from functions.machine_learning.gradient_BoostingV2.ModelEvaluation import (
    ModelEvaluation,
)
from functions.machine_learning.gradient_BoostingV2.ModelTraining import (
    ModelTraining,
)


class Result:
    def __init__(self, dados):
        self.dados = dados
        self.data_processor = DataProcessor()
        self.fe_engineer = None
        self.model_trainer = None
        self.model = None

    def run_pipeline(self):
        # Passo 1: Processar dados (sem scaling)
        processed_data = self.data_processor.process_raw_data(self.dados)

        # Passo 2: Engenharia de features
        self.fe_engineer = FeatureEngineering(processed_data)
        feature_df = self.fe_engineer.create_features()

        # Passo 3: Treinar modelo (com split e scaling correto)
        self.model_trainer = ModelTraining(feature_df, target_column="target")
        self.model_trainer.preprocess_data()
        self.model = self.model_trainer.train_model()

        # Passo 4: Avaliar
        evaluator = ModelEvaluation(
            self.model, self.model_trainer.X_test, self.model_trainer.y_test
        )
        metrics = evaluator.evaluate()
        print(metrics["classification_report"])
        evaluator.plot_confusion_matrix()

    @staticmethod
    def test_model():
        """
        Testa o pipeline completo com dados sintéticos.
        """
        # Criar dados sintéticos (30 dias)
        dates = pd.date_range(start="2023-01-01", periods=30, freq="D")
        np.random.seed(42)  # Para reproducibilidade

        # Gerar preços com variação significativa
        precos_fechamento = 100 + np.cumsum(np.random.uniform(-5, 5, 30))
        precos_fechamento = np.round(precos_fechamento, 2)

        data = {
            "Preço de Abertura": precos_fechamento,
            "Preço de Fechamento": precos_fechamento + np.random.uniform(-2, 2, 30),
            "Maxima Alta": precos_fechamento + np.random.uniform(1, 3, 30),
            "Minima Baixa": precos_fechamento - np.random.uniform(1, 3, 30),
            "Último RSI": np.random.uniform(30, 70, 30),
            "MACD": np.random.uniform(-1, 2, 30),
            "Última Volatilidade": np.random.uniform(0.5, 2.0, 30),
            "Diferença Atual": np.random.uniform(-2, 2, 30),
        }
        df = pd.DataFrame(data, index=dates)

        # Executar pipeline
        pipeline = Result(df)
        pipeline.run_pipeline()

        # Verificar previsões
        evaluator = ModelEvaluation(
            pipeline.model, pipeline.model_trainer.X_test, pipeline.model_trainer.y_test
        )
        print("\n💡 Resultado do Teste:")
        print("Acurácia:", evaluator.evaluate()["accuracy"])
        print("Matriz de Confusão:")
        evaluator.plot_confusion_matrix()


# Executar o teste
Result.test_model()
