import pandas as pd
from functions.logger import erro_logger


class TechnicalIndicators:
    """
    Classe para calcular indicadores técnicos.

    Attributes:
        stock_data (pd.DataFrame): DataFrame contendo os dados do ativo, com uma coluna 'close_price'.
        rsi_period (int): Período para o cálculo do RSI (padrão: 14).

    Methods:
        calculate_rsi(): Calcula o Índice de Força Relativa (RSI) e adiciona ao DataFrame.
    """

    def __init__(self, stock_data, rsi_period=5, adjusted=1):
        """
        Inicializa a classe TechnicalIndicators.

        Args:
            stock_data (pd.DataFrame): DataFrame com os dados do ativo. Deve conter uma coluna 'close_price'.
            rsi_period (int): Período para cálculo do RSI. Padrão: 14.
        """
        self.stock_data = stock_data
        self.rsi_period = rsi_period
        self.adjusted = adjusted

    def calculate_rsi(self):
        """
        Calcula o Índice de Força Relativa (RSI).

        Calcula o RSI usando a média móvel exponencial suavizada (SMMA) para ganhos e perdas.
        Adiciona uma nova coluna 'rsi' ao DataFrame stock_data.

        Returns:
            pd.DataFrame: O DataFrame stock_data com a coluna 'rsi' adicionada.
            None: se ocorrer algum erro.

        Raises:
            TypeError: Se stock_data não for um pandas DataFrame ou não contiver uma coluna 'close_price'.
            ValueError: se dados inválidos forem encontrados em 'close_price'
        """
        if not isinstance(self.stock_data, pd.DataFrame):
            raise TypeError("stock_data deve ser um pandas DataFrame.")

        if "close_price" not in self.stock_data.columns:
            raise TypeError("stock_data deve conter a coluna 'close_price'.")

        try:

            # Converte a coluna 'close_price' para numérico, substituindo erros por NaN
            self.stock_data["close_price"] = pd.to_numeric(
                self.stock_data["close_price"], errors="coerce"
            )

            # Calcula a diferença entre os preços de fechamento
            delta = self.stock_data["close_price"].diff()

            # Calcula os ganhos e perdas
            gain = delta.where(delta > 0, 0)
            loss = -delta.where(delta < 0, 0)

            # Calcula a SMMA dos ganhos e perdas
            avg_gain = gain.ewm(span=self.rsi_period, adjust=self.adjusted).mean()
            avg_loss = loss.ewm(span=self.rsi_period, adjust=self.adjusted).mean()

            # Calcula o RS e o RSI
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))

            # Adiciona o RSI ao DataFrame
            self.stock_data["rsi"] = rsi
            return self.stock_data

        except (ValueError, TypeError) as e:
            erro = f"Erro ao tentar executar calculate_rsi em Technical Indicator: {e}"
            erro_logger.error(erro)  # Registra a mensagem de erro no bot_logger.
            return None  # Retorna None em caso de erro.
