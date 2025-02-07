import logging
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns
import time
import numpy as np
from sklearn.metrics import (
    confusion_matrix,
    roc_curve,
    auc,
    precision_recall_curve,
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    classification_report,
)
from sklearn.calibration import label_binarize


class ModelVisualizer:
    def __init__(self, model, X_test, y_test):
        """
        Inicializa a classe com o modelo treinado e os dados de teste.

        Parâmetros:
        - model: modelo treinado
        - X_test: features de teste
        - y_test: rótulos reais de teste
        """
        self.model = model
        self.X_test = X_test
        self.y_test = y_test
        self.validate_data()  # Certifica-se de que os dados são válidos
        self.generate_predictions()

        # Obtém as classes únicas e ordenadas
        self.class_labels = sorted(np.unique(y_test))
        self.positive_count = (y_test == 1).sum()

        # Se for classificação binária, define o índice da classe 1
        if 1 in self.class_labels:
            self.idx = self.class_labels.index(1)
        else:
            self.idx = None

    def validate_data(self):
        """
        Valida os dados de entrada (X_test e y_test).
        """
        if self.X_test is None or self.y_test is None:
            st.error("X_test e y_test não podem ser None.")
            raise ValueError("X_test e y_test não podem ser None.")
        if len(self.X_test) != len(self.y_test):
            st.error("X_test e y_test devem ter o mesmo número de amostras.")
            raise ValueError("X_test e y_test devem ter o mesmo número de amostras.")

    def generate_predictions(self):
        """Obtém as predições e probabilidades do modelo, aplicando suavização se necessário."""
        try:
            self.y_pred = self.model.predict(self.X_test)
            self.y_prob = self.model.predict_proba(self.X_test)
            # Suavização de Laplace para evitar 0 ou 1 exatos
            self.y_prob = np.clip(self.y_prob, 1e-7, 1 - 1e-7)
        except AttributeError as e:
            st.error(
                "O modelo não possui o método predict_proba. Algumas métricas não serão calculadas."
            )
            self.y_prob = None
        except Exception as e:
            st.error(f"Erro ao obter previsões: {e}")
            self.y_pred = None
            self.y_prob = None

    def display_metrics(self):
        """
        Calcula e exibe as principais métricas do modelo, além do relatório de classificação
        e da distribuição das classes.
        """
        accuracy = accuracy_score(self.y_test, self.y_pred)
        precision = precision_score(self.y_test, self.y_pred, average="weighted")
        recall = recall_score(self.y_test, self.y_pred, average="weighted")
        f1 = f1_score(self.y_test, self.y_pred, average="weighted")
        try:
            auc_roc = roc_auc_score(self.y_test, self.y_prob, multi_class="ovr")
        except Exception:
            auc_roc = None

        st.subheader("Métricas do Modelo")
        st.write(f"**Acurácia:** {accuracy:.4f}")
        st.write(f"**Precisão:** {precision:.4f}")
        st.write(f"**Recall:** {recall:.4f}")
        st.write(f"**F1-Score:** {f1:.4f}")
        if auc_roc is not None:
            st.write(f"**AUC-ROC:** {auc_roc:.4f}")

        st.text("Relatório de Classificação")
        st.text(classification_report(self.y_test, self.y_pred))
        st.write("Distribuição das classes:")
        distrib = {cls: int(sum(self.y_test == cls)) for cls in self.class_labels}
        st.write(distrib)

    def plot_confusion_matrix(self):
        """Plota a matriz de confusão usando Seaborn."""
        cm = confusion_matrix(self.y_test, self.y_pred)
        fig, ax = plt.subplots(figsize=(8, 6))
        sns.heatmap(
            cm,
            annot=True,
            fmt="d",
            cmap="Blues",
            xticklabels=self.class_labels,
            yticklabels=self.class_labels,
            ax=ax,
        )
        ax.set_xlabel("Previsão")
        ax.set_ylabel("Real")
        ax.set_title("Matriz de Confusão")
        st.pyplot(fig)

    def plot_roc_curve(self):
        try:
            if self.y_prob is None:
                raise ValueError("Chame 'evaluate' antes de plotar a curva ROC.")

            # Obtenha as classes usadas no treinamento (por exemplo, [-1, 0, 1])
            classes = self.model.classes_
            # Converta y_test para formato binário (One-vs-Rest)
            y_test_bin = label_binarize(self.y_test, classes=classes)
            n_classes = y_test_bin.shape[1]

            fpr = dict()
            tpr = dict()
            roc_auc = dict()
            for i in range(n_classes):
                fpr[i], tpr[i], _ = roc_curve(y_test_bin[:, i], self.y_prob[:, i])
                roc_auc[i] = auc(fpr[i], tpr[i])

            plt.figure(figsize=(10, 8))
            for i, cl in enumerate(classes):
                plt.plot(
                    fpr[i],
                    tpr[i],
                    label=f"Classe {cl} (AUC = {roc_auc[i]:.2f})",
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

    def plot_precision_recall_curve(self):
        try:
            if self.y_prob is None:
                raise ValueError(
                    "Chame 'evaluate' antes de plotar a curva Precisão-Recall."
                )

            # Obtenha as classes usadas no treinamento
            classes = self.model.classes_
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

    def plot_precision_vs_threshold(self):
        """
        Plota a curva de Precisão vs Limiar de Decisão.
        Essa função suporta apenas problemas binários.
        """
        if len(self.class_labels) != 2:
            st.warning(
                "plot_precision_vs_threshold suporta apenas classificação binária."
            )
            return

        y_test_bin = (self.y_test == 1).astype(int)
        y_prob = self.y_prob[:, 1]
        precision, recall, thresholds = precision_recall_curve(y_test_bin, y_prob)
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.plot(thresholds, precision[:-1], label="Precisão", linestyle="--")
        ax.plot(thresholds, recall[:-1], label="Recall")
        ax.set_xlabel("Limiar de Decisão")
        ax.set_ylabel("Valor")
        ax.set_title("Precisão vs Limiar de Decisão")
        ax.legend()
        st.pyplot(fig)

    def run_dashboard(self, epochs=5, sleep_time=2):
        """
        Executa o dashboard completo com uma barra de progresso, exibe as métricas e as
        visualizações: Matriz de Confusão, ROC, Precisão-Recall e Precisão vs Threshold.

        Parâmetros:
        - epochs: número de iterações para simular progresso (por exemplo, de treinamento)
        - sleep_time: tempo de espera entre iterações (simula tempo de treinamento)
        """
        st.title("Dashboard de Avaliação do Modelo")
        progress_bar = st.progress(0)

        # Simulação de progresso (pode ser adaptado para acompanhar treinamento real)
        for epoch in range(1, epochs + 1):
            st.subheader(f"Época {epoch}")
            time.sleep(sleep_time)
            progress_bar.progress(int(epoch * 100 / epochs))

        # Exibe as métricas calculadas
        self.display_metrics()

        st.subheader("Visualizações")
        with st.expander("Matriz de Confusão"):
            self.plot_confusion_matrix()
        with st.expander("Curva ROC"):
            self.plot_roc_curve()
        with st.expander("Curva Precisão-Recall"):
            self.plot_precision_recall_curve()
        with st.expander("Precisão vs Limiar de Decisão"):
            self.plot_precision_vs_threshold()
