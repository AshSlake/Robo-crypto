import pandas as pd

class TechnicalIndicators:
    def __init__(self, stock_data, rsi_period=5):
        self.stock_data = stock_data
        self.rsi_period = rsi_period

    def calculate_rsi(self):
        """
        Calcula o Índice de Força Relativa (RSI) para os dados de ações fornecidos.

        O cálculo é baseado no período definido durante a inicialização da classe.
        """
        # Converte a coluna 'close_price' para numérico, substituindo erros por NaN
        self.stock_data['close_price'] = pd.to_numeric(self.stock_data['close_price'], errors='coerce')

        # Calcula a diferença
        delta = self.stock_data['close_price'].diff()

        # Calcula os valores de ganho e perda para cada período
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)

        # Calcula a média móvel dos ganhos e perdas
        avg_gain = gain.rolling(window=self.rsi_period, min_periods=1).mean()
        avg_loss = loss.rolling(window=self.rsi_period, min_periods=1).mean()

        # Calcula o RSI usando os valores de ganho e perda
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        # Adiciona o RSI ao DataFrame
        self.stock_data['rsi'] = rsi
        return self.stock_data

# Exemplo de uso
# stock_data = pd.DataFrame({'close_price': [dados_aqui]})
# ti = TechnicalIndicators(stock_data)
# rsi_values = ti.calculate_rsi()
# print(stock_data)
