import logging
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.calibration import label_binarize
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
)
from sklearn.metrics import confusion_matrix, roc_curve, auc, precision_recall_curve
from sklearn.metrics import mean_squared_error
import numpy as np

# Configura o logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


class ModelEvaluation:
    def __init__(self, model, X_test, y_test):
        """
        Inicializa a classe de avaliação de modelo.

        Parâmetros:
        - model: o modelo treinado a ser avaliado.
        - X_test: as features de teste.
        - y_test: as labels de teste.
        """
        self.model = model
        self.X_test = X_test
        self.y_test = y_test
        self.validate_data()
        try:
            self.y_pred = self.model.predict(self.X_test)
            self.y_prob = self.model.predict_proba(self.X_test)
            # Suavização de Laplace
            self.y_prob = np.clip(self.y_prob, 1e-7, 1 - 1e-7)
        except AttributeError:
            logging.error(
                "O modelo não possui o método predict_proba. Algumas métricas não serão calculadas."
            )
            self.y_prob = None
        except Exception as e:
            logging.error(f"Erro ao obter previsões: {e}")
            self.y_pred = None
            self.y_prob = None

    def validate_data(self):
        """
        Valida os dados de entrada (X_test e y_test).
        """
        if self.X_test is None or self.y_test is None:
            raise ValueError("X_test e y_test não podem ser None.")
        if len(self.X_test) != len(self.y_test):
            raise ValueError("X_test e y_test devem ter o mesmo número de amostras.")

    def get_model_probabilities(self):
        """Retorna as probabilidades previstas, com suavização se necessário."""
        probs = self.model.predict_proba(self.X_test)

        # Suavização de Laplace (apenas se necessário)
        if np.any((probs == 0) | (probs == 1)):  # Verifique se há 0 ou 1
            probs = np.clip(probs, 1e-7, 1 - 1e-7)

        return probs

    def evaluate(self):
        """Avalia o modelo com métricas, incluindo AUC-ROC multiclasse."""

        self.y_pred = self.model.predict(self.X_test)  # Calcular y_pred uma vez
        self.y_prob = self.get_model_probabilities()  # Calcular y_prob uma vez

        y_true = self.y_test

        accuracy = accuracy_score(y_true, self.y_pred)
        precision = precision_score(y_true, self.y_pred, average="weighted")
        recall = recall_score(y_true, self.y_pred, average="weighted")
        f1 = f1_score(y_true, self.y_pred, average="weighted")

        # Calcular AUC-ROC multiclasse
        auc_roc = roc_auc_score(self.y_test, self.y_prob, multi_class="ovr")  # ou 'ovo'

        # self._display_metrics(accuracy, precision, recall, f1, auc_roc)

        return accuracy, precision, recall, f1, auc_roc

    def _display_metrics(self, accuracy, precision, recall, f1, auc_roc):
        """
        Exibe as métricas principais de avaliação.
        """
        logging.info(f"Acurácia: {accuracy:.4f}")
        logging.info(f"Precisão: {precision:.4f}")
        logging.info(f"Recall: {recall:.4f}")
        logging.info(f"F1-Score: {f1:.4f}")
        logging.info(f"AUC-ROC: {auc_roc:.4f}")

    def plot_confusion_matrix(self, class_labels):
        """
        Plota a matriz de confusão com rótulos personalizados.
        """
        if self.y_pred is None:  # Verificar se já foi calculado
            self.y_pred = self.model.predict(self.X_test)
        confusion = confusion_matrix(self.y_test, self.y_pred)

        plt.figure(figsize=(8, 6))
        sns.heatmap(
            confusion,
            annot=True,
            fmt="d",
            cmap="Blues",
            xticklabels=class_labels,
            yticklabels=class_labels,
        )
        plt.xlabel("Previsão")
        plt.ylabel("Real")
        plt.title("Matriz de Confusão")
        plt.show()

    def plot_roc_curve(self):
        try:
            if self.y_prob is None:
                raise ValueError("Chame 'evaluate' antes de plotar a curva ROC.")

            # Calcular AUC-ROC para cada classe (OvR)
            n_classes = self.y_prob.shape[1]
            fpr = dict()
            tpr = dict()
            roc_auc = dict()
            for i in range(n_classes):
                fpr[i], tpr[i], _ = roc_curve(self.y_test == i, self.y_prob[:, i])
                roc_auc[i] = auc(fpr[i], tpr[i])

            # Plotar as curvas ROC para cada classe
            plt.figure(figsize=(10, 8))
            for i in range(n_classes):
                plt.plot(
                    fpr[i],
                    tpr[i],
                    label=f"Classe {i} (AUC = {roc_auc[i]:.2f})",
                )
            plt.plot([0, 1], [0, 1], "k--")
            plt.xlim([0.0, 1.0])
            plt.ylim([0.0, 1.05])
            plt.xlabel("Taxa de Falsos Positivos")
            plt.ylabel("Taxa de Verdadeiros Positivos")
            plt.title("Curva ROC (multiclasse)")
            plt.legend(loc="lower right")
            plt.show()
        except Exception as e:
            logging.error(f"Erro ao plotar a curva ROC: {e}")
        except ValueError as e:
            logging.error(f"Erro ao calcular métricas: {e}")

    def plot_precision_recall_curve(self):
        """
        Plota a curva de Precisão e Recall.
        """
        try:
            if self.y_prob is None:
                raise ValueError(
                    "Chame 'evaluate' antes de plotar a curva Precisão-Recall."
                )

            precision, recall, _ = precision_recall_curve(
                self.y_test, self.y_prob
            )  # Usar self.y_prob

            plt.figure(figsize=(8, 6))
            plt.plot(recall, precision, color="blue", lw=2)
            plt.xlabel("Recall")
            plt.ylabel("Precisão")
            plt.title("Curva de Precisão e Recall")
            plt.show()
        except Exception as e:
            logging.error(f"Erro ao plotar a curva Precisão-Recall: {e}")
        except ValueError as e:
            logging.error(f"Erro ao calcular métricas: {e}")

    def get_additional_metrics(self, y_pred, y_prob):
        """
        Calcula métricas adicionais como MSE e AUC-ROC.
        """
        mse = mean_squared_error(self.y_test, y_pred)
        auc_roc = roc_auc_score(self.y_test, y_prob)
        return mse, auc_roc

    def analyze_errors(self, y_pred):
        """
        Analisa os erros cometidos pelo modelo e exibe as amostras mal classificadas.
        """
        errors = y_pred != self.y_test
        misclassified = self.X_test[errors]

        # Visualizar ou salvar os exemplos errados, se necessário.
        print("Exemplos mal classificados:")
        print(misclassified)

    def get_y_pred(self):
        if self.y_pred is None:
            self.y_pred = self.model.predict(
                self.X_test
            )  # Calcule aqui se ainda não tiver sido calculado
        return self.y_pred

    @staticmethod
    def calculate_metrics(y_test, y_pred, y_prob=None):
        """
        Calcula métricas como AUC-ROC, Precisão, Recall e Exatidão.

        :param y_test: Valores reais (rótulos)
        :param y_pred: Previsões do modelo
        :param y_prob: Probabilidades preditas (opcional, necessário para AUC-ROC)
        """
        unique, counts = np.unique(y_test, return_counts=True)
        print(
            f"Distribuição das classes no conjunto de teste: {dict(zip(unique, counts))}"
        )

        if len(unique) == 1:
            print(
                "⚠️ AVISO: O conjunto de teste contém apenas uma classe. Algumas métricas podem não ser calculadas."
            )

        # Métricas comuns
        print("\nRelatório de Classificação:\n", classification_report(y_test, y_pred))
        print(f"Acurácia: {accuracy_score(y_test, y_pred):.4f}")

        # Calcular AUC-ROC somente se houver mais de uma classe
        if y_prob is not None and len(unique) > 1:
            try:
                auc_score = roc_auc_score(y_test, y_prob, multi_class="ovr")
                print(f"AUC-ROC Score (One-vs-Rest): {auc_score:.4f}")
            except ValueError as e:
                print(f"Erro ao calcular AUC-ROC: {e}")

    @staticmethod
    def plot_precision_recall(y_test, y_prob):
        """
        Plota a curva Precisão-Recall para problemas binários e multiclasse.

        :param y_test: Valores reais (rótulos)
        :param y_prob: Probabilidades preditas do modelo
        """
        classes = np.unique(y_test)

        if len(classes) == 1:
            print(
                "⚠️ Não é possível plotar a curva Precisão-Recall porque há apenas uma classe no conjunto de teste."
            )
            return

        # Converter para formato binário (One-vs-Rest)
        y_test_bin = label_binarize(y_test, classes=classes)

        plt.figure(figsize=(8, 6))

        for i in range(y_test_bin.shape[1]):
            precision, recall, _ = precision_recall_curve(
                y_test_bin[:, i], y_prob[:, i]
            )
            plt.plot(recall, precision, label=f"Classe {classes[i]}")

        plt.xlabel("Recall")
        plt.ylabel("Precisão")
        plt.title("Curva Precisão-Recall (One-vs-Rest)")
        plt.legend()
        plt.grid()
        plt.show()

    @staticmethod
    def plot_precision_vs_threshold(y_test, y_prob):
        """
        Plota a precisão em relação ao limiar de decisão.

        :param y_test: Valores reais (rótulos)
        :param y_prob: Probabilidades preditas
        """
        if len(np.unique(y_test)) > 2:
            print("⚠️ plot_precision_vs_threshold suporta apenas classificação binária.")
            return

        precision, recall, thresholds = precision_recall_curve(y_test, y_prob)

        plt.figure(figsize=(8, 6))
        plt.plot(thresholds, precision[:-1], label="Precisão", linestyle="--")
        plt.plot(thresholds, recall[:-1], label="Recall")
        plt.xlabel("Limiar de Decisão")
        plt.ylabel("Precisão / Recall")
        plt.title("Precisão vs Limiar de Decisão")
        plt.legend()
        plt.grid()
        plt.show()
