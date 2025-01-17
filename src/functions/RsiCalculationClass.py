import pandas as pd


class TechnicalIndicators:
    def __init__(self, stock_data, rsi_period=14):
        self.stock_data = stock_data
        self.rsi_period = rsi_period

    def calculate_rsi(self):
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
        avg_gain = gain.ewm(span=self.rsi_period, adjust=False).mean()
        avg_loss = loss.ewm(span=self.rsi_period, adjust=False).mean()

        # Calcula o RS e o RSI
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        # Adiciona o RSI ao DataFrame
        self.stock_data["rsi"] = rsi
        return self.stock_data


# Exemplo de uso
# stock_data = pd.DataFrame({'close_price': [dados_aqui]})
# ti = TechnicalIndicators(stock_data, rsi_period=14)
# rsi_values = ti.calculate_rsi()
# print(stock_data)
