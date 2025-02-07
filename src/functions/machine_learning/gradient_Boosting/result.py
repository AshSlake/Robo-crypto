# result.py
import logging
import os
from functions.machine_learning.gradient_Boosting.model_training import (
    ModelTraining as model_training,
)
from functions.machine_learning.gradient_Boosting.feature_engineering import (
    FeatureEngineering as feature_engineering,
)
from functions.machine_learning.gradient_Boosting.data_processing import (
    DataProcessor as data_processing,
)
from functions.machine_learning.gradient_Boosting.model_evaluation import (
    ModelEvaluation as model_evaluation,
)
from sklearn.model_selection import train_test_split
import pandas as pd
import joblib
from imblearn.over_sampling import SMOTE
from functions.machine_learning.ModelVisualizer import ModelVisualizer

model_dir = "model"
os.makedirs(model_dir, exist_ok=True)
gradient_Boosting = os.path.join(model_dir, "model_gradient_boosting")
gradient_Boosting = os.path.abspath(gradient_Boosting)  # Tornar o caminho absoluto

os.makedirs(gradient_Boosting, exist_ok=True)
os.environ["LOKY_MAX_CPU_COUNT"] = "4"  # Define um número seguro de núcleos


class Result:
    def __init__(self, dados, test_size=0.2, use_grid_search=True):
        """
        Inicializa a classe Result com os dados.

        Parâmetros:
        dados: Dados formatados que serão passados ao modelo para treinamento e previsão.
        test_size: float
            A fração dos dados que será usada como conjunto de teste.
        use_grid_search: bool
            Se True, utiliza a busca em grade para otimizar os hiperparâmetros do modelo.
        """
        self.dados = dados
        self.test_size = test_size
        self.use_grid_search = use_grid_search
        self.model = self.load_model(
            model_filename=os.path.join(
                gradient_Boosting, "gradient_boosting_model.joblib"
            )
        )  # Carrega o modelo caso ele já tenha sido treinado anteriormente

        self.features = None  # As features processadas serão armazenadas aqui
        self.X_test = None
        self.y_test = None
        self.X_train = None
        self.y_train = None
        self.predictions = None  # Inicializa predictions como None
        self.train_model()  # Chama o treinamento

    def train_model(self):
        """
        Treina o modelo utilizando os dados fornecidos.

        O método usa a classe ModelTraining para treinar o modelo.
        """
        # Passo 1: Pré-processamento dos dados
        print("Pré-processando os dados...")
        data_processor = data_processing(False)
        processed_data = data_processor.process_raw_data(self.dados)

        fe = feature_engineering(processed_data)
        # Criar a variável alvo após a engenharia de features para evitar problemas
        processed_data = fe.create_features(processed_data)

        # Criar a variável alvo corretamente
        processed_data["target"] = processed_data.apply(fe.generate_target, axis=1)

        # Verificar distribuição das classes antes de seguir
        if processed_data["target"].nunique() < 2:
            print(processed_data["target"].value_counts())
            raise ValueError("Erro: Apenas uma classe detectada. Revise os dados.")

        processed_data = fe.clean_data(processed_data)
        self.features = processed_data

        print("Pré-processamento concluído.")

        # Passo 2: Engenharia de características
        print("Engenhando as características...")
        print(
            "Criando novas features para melhorar a qualidade dos dados de entrada do modelo."
        )
        new_columns = fe.evaluate_feature_importance(
            processed_data, target_column="target"
        )
        # Pegamos os nomes das features selecionadas
        selected_columns = new_columns["Feature"].tolist()
        # Garantir que a variável alvo ainda está no DataFrame
        selected_columns.append("target")
        # Aplicar a seleção ao DataFrame original
        self.features = self.features[selected_columns]
        print("Engenharia de características concluída.")

        # Passo 3: Divisão dos dados em treino e teste
        print("Dividindo os dados em treino e teste...")
        self._split_data()
        print("Divisão dos dados concluída.")

        # Passo 4: Treinamento do modelo
        print("Iniciando o treinamento do modelo...")
        model_trainer = model_training(self.features, target_column="target")
        model_trainer.preprocess_data()
        self.model = model_trainer.train_model()
        print("Modelo treinado com sucesso.")

        # Passo 5: Avaliação do modelo
        print("Avaliação do modelo...")
        model_evaluator = model_evaluation(self.model, self.X_test, self.y_test)
        evaluation_results = model_evaluator.evaluate()
        print("Avaliação do modelo concluída.")

        # Armazenando a avaliação para uso posterior, se necessário
        self.evaluation_results = evaluation_results

        # Exibindo métricas adicionais
        print("Exibindo métricas adicionais...")
        self._plot_additional_metrics(model_evaluator)

        # visualizer = ModelVisualizer(self.model, self.X_test, self.y_test)
        # visualizer.run_dashboard(epochs=5, sleep_time=2)

        self.train_and_save_model(
            model_filename=os.path.join(
                gradient_Boosting, "gradient_boosting_model.joblib"
            )
        )  # passar explicitamente

        # Fazer a predição e armazenar em self.predictions
        predicao = self.model.predict(self.X_test)
        self.predictions = {
            "predicoes": predicao.tolist(),
            "shape": predicao.shape,
            "tipo": str(type(predicao)),
        }
        return self.predictions  # Retorna as predições

    def predict(self):
        """
        Retorna as predições do modelo para os dados de teste.
        """
        if self.model is None:
            raise ValueError("Modelo não treinado. Execute train_model primeiro.")

        if self.predictions is None:
            predicao = self.model.predict(self.X_test)
            self.predictions = {
                "predicoes": predicao.tolist(),
                "shape": predicao.shape,
                "tipo": str(type(predicao)),
            }

        return self.predictions

    def train_and_save_model(self, model_filename=None):
        if model_filename is None:  # Manter o if para permitir flexibilidade
            model_filename = os.path.join(
                gradient_Boosting, "gradient_boosting_model.joblib"
            )

        try:
            joblib.dump(self.model, model_filename)
        # print(f"Modelo Gradient Boosting salvo em {model_filename}")
        except Exception as e:
            logging.error(f"Erro ao salvar o modelo Gradient Boosting: {e}")

    def load_model(self, model_filename=None):
        """Carrega o modelo Gradient Boosting salvo a partir de um arquivo.

        Args:
            model_filename (str, optional): O caminho para o arquivo do modelo.
                                            Se None, usa o caminho padrão.
        """
        if model_filename is None:
            model_filename = os.path.join(
                gradient_Boosting, "gradient_boosting_model.joblib"
            )

        try:
            self.model = joblib.load(model_filename)
            logging.info(f"Modelo Gradient Boosting carregado de {model_filename}")
        except FileNotFoundError:
            logging.error(
                f"Arquivo do modelo Gradient Boosting não encontrado: {model_filename}"
            )
            self.model = (
                None  # Garante que o modelo seja None se o arquivo não for encontrado
            )
        except Exception as e:
            logging.error(f"Erro ao carregar o modelo Gradient Boosting: {e}")
            self.model = None  # Garante que o modelo seja None em caso de erro

    def make_predictions_on_new_data(self, new_data_raw):
        """Faz previsões em novos dados brutos (unseen)."""

        if self.model is None:
            raise ValueError("Modelo não treinado. Não é possível fazer previsões.")

        # 1. Pré-processamento dos novos dados (igual ao treinamento)
        print("iniciando pré-processamento dos novos dados...")
        data_processor = data_processing(False)
        processed_new_data = data_processor.process_raw_data(new_data_raw)
        print("novos dados processados concluídos.")

        fe = feature_engineering()
        # 2. Engenharia de features (igual ao treinamento)
        print("iniciando engenharia de features...")
        processed_new_data = fe.create_features(processed_new_data)
        processed_new_data["target"] = processed_new_data.apply(
            fe.generate_target, axis=1
        )
        processed_new_data = fe.clean_data(processed_new_data)

        selected_columns = (
            fe.get_selected_features()
        )  # Obter as features selecionadas durante o treinamento (importante!)
        selected_columns.append("target")  # Adicionar o target (se ainda não estiver)
        processed_new_data = processed_new_data[selected_columns]
        print("novos dados engenharia de features concluída.")

        # 3. Selecionar apenas as colunas usadas no treinamento (IMPORTANTE!)
        print("Selecionando apenas as colunas usadas no treinamento...")
        X_new = processed_new_data.drop(
            columns=["target"]
        )  # Remover a coluna alvo, se presente

        # 4. Aplicar o mesmo scaler usado no treinamento (se aplicável):
        print("Aplicando o mesmo scaler...")
        X_new[self.model_trainer.num_cols] = self.model_trainer.scaler.transform(
            X_new[self.model_trainer.num_cols]
        )

        # 5. Fazer as previsões
        print("Fazendo previsões...")
        predictions = self.model.predict(X_new)

        return predictions

    def _split_data(self):
        # Garantir que "target" está no dataset
        if "target" not in self.features.columns:
            raise ValueError("Erro: A variável alvo 'target' não foi encontrada.")

        # Separar X e y corretamente
        X = self.features.drop(columns=["target"])
        y = self.features["target"]

        # print("Distribuição de classes ANTES da divisão:")
        # print(y.value_counts())

        # Aplique SMOTE antes da divisão treino/teste
        # oversample = SMOTE()
        # X, y = oversample.fit_resample(
        #    X, y
        # )  # X e y são seus dados de features e target

        # Divisão treino/teste usando train_test_split
        self.X_train, self.X_test, self.y_train, self.y_test = train_test_split(
            X, y, test_size=self.test_size, random_state=42, stratify=y
        )

        # Imprimir os shapes para verificar se a divisão foi bem-sucedida

        # print(
        #    f"X_train shape: {self.X_train.shape}, y_train shape: {self.y_train.shape}"
        # )
        # print(f"X_test shape: {self.X_test.shape}, y_test shape: {self.y_test.shape}")

        # print("Distribuição de classes no conjunto de TREINO:")
        # print(self.y_train.value_counts())
        # print("Distribuição de classes no conjunto de TESTE:")
        # print(self.y_test.value_counts())

    def _plot_additional_metrics(self, model_evaluator):
        try:
            # Supondo que self.y_test contenha os rótulos originais (0, 1 e -1)
            # Convertemos para binário: 1 permanece 1; os demais tornam-se 0.
            y_test_binary = (self.y_test == 1).astype(int)

            # Obter as probabilidades preditas (supondo que a previsão seja para 3 classes)
            y_prob = self.model.predict_proba(self.X_test)

            # Se o modelo foi treinado em um problema multiclasse, precisamos identificar a probabilidade da classe 1.
            # Vamos assumir que as classes foram ordenadas e que a classe 1 corresponde ao índice apropriado.
            # Para garantir, podemos ordenar os rótulos:
            positive_count = (self.y_test == 1).sum()
            class_labels = sorted(self.y_test.unique())
            print("Classes originais:", class_labels)
            # Encontre o índice correspondente à classe 1
            if 1 in class_labels:
                idx = class_labels.index(1)
            else:
                raise ValueError("A classe 1 não está presente em y_test.")

            # Extraia as probabilidades para a classe 1
            y_prob_positive_class = y_prob[:, idx]
            model_evaluator.plot_confusion_matrix(class_labels)
            y_prob = self.model.predict_proba(self.X_test)
            if y_prob.shape[1] < 2:
                print(
                    "Aviso: Não é possível plotar a curva ROC. Apenas uma classe prevista."
                )
            else:
                if len(class_labels) == 2:
                    y_prob_positive_class = y_prob[:, 1]
                else:
                    y_prob_positive_class = y_prob[:, class_labels.index(1)]

            model_evaluator.plot_roc_curve()
            model_evaluator.plot_precision_recall_curve()

            if positive_count == 0:
                print(
                    "Aviso: Não há amostras positivas em y_test. A curva Precisão-Recall não pode ser plotada."
                )
            else:
                model_evaluator.plot_precision_vs_threshold(
                    y_test_binary, y_prob_positive_class
                )
            print("Distribuição de y_test:", self.y_test.value_counts())

        except ValueError as e:
            print(f"Erro ao plotar métricas adicionais: {e}")
        except Exception as e:
            print(f"Erro inesperado ao plotar: {e}")

    def analyze_model_errors(self):
        """
        Analisa e exibe amostras mal classificadas pelo modelo.
        """
        y_pred = self.model.predict(self.X_test)
        model_evaluator = model_evaluation(self.model, self.X_test, self.y_test)
        model_evaluator.analyze_errors(y_pred)
