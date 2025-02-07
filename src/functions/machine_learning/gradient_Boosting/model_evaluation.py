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
    confusion_matrix,
    roc_curve,
    auc,
    precision_recall_curve,
    mean_squared_error,
)
import numpy as np

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


class ModelEvaluation:
    def __init__(self, model, X_test, y_test):
        self.model = model
        self.X_test = X_test
        self.y_test = y_test
        self.validate_data()
        try:
            self.y_pred = self.model.predict(self.X_test)
            if hasattr(self.model, "predict_proba"):
                self.y_prob = self.model.predict_proba(self.X_test)
                self.y_prob = np.clip(self.y_prob, 1e-7, 1 - 1e-7)
            else:
                logging.warning(
                    "O modelo não possui o método predict_proba. Algumas métricas não serão calculadas."
                )
                self.y_prob = None
        except Exception as e:
            logging.error(f"Erro ao obter previsões: {e}")
            self.y_pred = None
            self.y_prob = None

    def validate_data(self):
        if self.X_test is None or self.y_test is None:
            raise ValueError("X_test e y_test não podem ser None.")
        if len(self.X_test) != len(self.y_test):
            raise ValueError("X_test e y_test devem ter o mesmo número de amostras.")

    def get_model_probabilities(self):
        probs = self.model.predict_proba(self.X_test)
        if np.any((probs == 0) | (probs == 1)):
            probs = np.clip(probs, 1e-7, 1 - 1e-7)
        return probs

    def evaluate(self):
        y_true = self.y_test
        accuracy = accuracy_score(y_true, self.y_pred)
        precision = precision_score(y_true, self.y_pred, average="weighted")
        recall = recall_score(y_true, self.y_pred, average="weighted")
        f1 = f1_score(y_true, self.y_pred, average="weighted")

        try:
            if self.y_prob is not None and len(np.unique(y_true)) > 1:
                auc_roc = roc_auc_score(y_true, self.y_prob, multi_class="ovr")
            else:
                auc_roc = None
                logging.warning(
                    "AUC-ROC não pode ser calculado pois há apenas uma classe."
                )
        except Exception as e:
            auc_roc = None
            logging.error(f"Erro ao calcular AUC-ROC: {e}")

        return accuracy, precision, recall, f1, auc_roc

    def plot_confusion_matrix(self):
        if self.y_pred is None:
            self.y_pred = self.model.predict(self.X_test)
        confusion = confusion_matrix(self.y_test, self.y_pred)
        plt.figure(figsize=(8, 6))
        sns.heatmap(confusion, annot=True, fmt="d", cmap="Blues")
        plt.xlabel("Previsão")
        plt.ylabel("Real")
        plt.title("Matriz de Confusão")
        plt.show()

    def plot_roc_curve(self):
        try:
            if self.y_prob is None:
                raise ValueError("Chame 'evaluate' antes de plotar a curva ROC.")

            classes = (
                self.model.classes_
                if hasattr(self.model, "classes_")
                else np.unique(self.y_test)
            )
            y_test_bin = label_binarize(self.y_test, classes=classes)
            n_classes = y_test_bin.shape[1]
            fpr, tpr, roc_auc = {}, {}, {}

            for i in range(n_classes):
                fpr[i], tpr[i], _ = roc_curve(y_test_bin[:, i], self.y_prob[:, i])
                roc_auc[i] = auc(fpr[i], tpr[i])

            plt.figure(figsize=(10, 8))
            for i, cl in enumerate(classes):
                plt.plot(fpr[i], tpr[i], label=f"Classe {cl} (AUC = {roc_auc[i]:.2f})")

            plt.plot([0, 1], [0, 1], "k--")
            plt.xlabel("Taxa de Falsos Positivos")
            plt.ylabel("Taxa de Verdadeiros Positivos")
            plt.title("Curva ROC (multiclasse)")
            plt.legend(loc="lower right")
            plt.show()
        except Exception as e:
            logging.error(f"Erro ao plotar a curva ROC: {e}")

    def plot_precision_recall_curve(self):
        try:
            if self.y_prob is None:
                raise ValueError(
                    "Chame 'evaluate' antes de plotar a curva Precisão-Recall."
                )

            classes = (
                self.model.classes_
                if hasattr(self.model, "classes_")
                else np.unique(self.y_test)
            )
            y_test_bin = label_binarize(self.y_test, classes=classes)
            n_classes = y_test_bin.shape[1]
            plt.figure(figsize=(10, 8))

            for i in range(n_classes):
                precision, recall, _ = precision_recall_curve(
                    y_test_bin[:, i], self.y_prob[:, i]
                )
                plt.plot(recall, precision, lw=2, label=f"Classe {classes[i]}")

            plt.xlabel("Recall")
            plt.ylabel("Precisão")
            plt.title("Curva Precisão-Recall (One-vs-Rest)")
            plt.legend()
            plt.grid(True)
            plt.show()
        except Exception as e:
            logging.error(f"Erro ao plotar a curva Precisão-Recall: {e}")

    def get_additional_metrics(self, y_pred, y_prob):
        mse = mean_squared_error(self.y_test, y_pred)
        auc_roc = roc_auc_score(self.y_test, y_prob, multi_class="ovr")
        return mse, auc_roc

    def analyze_errors(self, y_pred):
        errors = y_pred != self.y_test
        misclassified = self.X_test[errors]
        print("Exemplos mal classificados:")
        print(misclassified)

    @staticmethod
    def calculate_metrics(y_test, y_pred, y_prob=None):
        unique, counts = np.unique(y_test, return_counts=True)
        print(
            f"Distribuição das classes no conjunto de teste: {dict(zip(unique, counts))}"
        )
        if len(unique) == 1:
            print(
                "⚠️ AVISO: O conjunto de teste contém apenas uma classe. Algumas métricas podem não ser calculadas."
            )
        print("\nRelatório de Classificação:\n", classification_report(y_test, y_pred))
        print(f"Acurácia: {accuracy_score(y_test, y_pred):.4f}")
        if y_prob is not None and len(unique) > 1:
            try:
                auc_score = roc_auc_score(y_test, y_prob, multi_class="ovr")
                print(f"AUC-ROC Score (One-vs-Rest): {auc_score:.4f}")
            except ValueError as e:
                print(f"Erro ao calcular AUC-ROC: {e}")

    @staticmethod
    def plot_precision_recall(y_test, y_prob):
        if y_prob is None:
            print(
                "⚠️ Não há probabilidades disponíveis para plotar a curva Precisão-Recall."
            )
            return
        classes = np.unique(y_test)
        if len(classes) == 1:
            print(
                "⚠️ Não é possível plotar a curva Precisão-Recall porque há apenas uma classe no conjunto de teste."
            )
            return
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
        if y_prob is None or len(np.unique(y_test)) > 2:
            print(
                "⚠️ plot_precision_vs_threshold suporta apenas classificação binária com probabilidades válidas."
            )
            return
        precision, recall, thresholds = precision_recall_curve(y_test, y_prob[:, 1])
        plt.figure(figsize=(8, 6))
        plt.plot(thresholds, precision[:-1], label="Precisão", linestyle="--")
        plt.plot(thresholds, recall[:-1], label="Recall")
        plt.xlabel("Limiar de Decisão")
        plt.ylabel("Precisão / Recall")
        plt.title("Precisão vs Limiar de Decisão")
        plt.legend()
        plt.grid()
        plt.show()
