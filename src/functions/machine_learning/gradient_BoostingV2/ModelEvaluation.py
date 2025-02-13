# model_evaluation.py
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    roc_auc_score,
    confusion_matrix,
)
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import logging

logging.basicConfig(level=logging.INFO)


class ModelEvaluation:
    def __init__(self, model, X_test, y_test):
        self.model = model
        self.X_test = X_test
        self.y_test = y_test
        self.y_pred = model.predict(X_test)
        self.y_prob = self._safe_predict_proba()

    def _safe_predict_proba(self):
        try:
            return self.model.predict_proba(self.X_test)
        except AttributeError:
            logging.warning("Modelo não suporta predict_proba.")
            return None

    def evaluate(self):
        """Retorna métricas principais."""
        report = classification_report(self.y_test, self.y_pred)
        accuracy = accuracy_score(self.y_test, self.y_pred)
        auc_roc = (
            roc_auc_score(self.y_test, self.y_prob, multi_class="ovr")
            if self.y_prob is not None
            else None
        )

        return {
            "classification_report": report,
            "accuracy": accuracy,
            "auc_roc": auc_roc,
        }

    def plot_confusion_matrix(self):
        cm = confusion_matrix(self.y_test, self.y_pred)
        plt.figure(figsize=(10, 7))
        sns.heatmap(cm, annot=True, fmt="d", cmap="Blues")
        plt.title("Matriz de Confusão")
        plt.show()
