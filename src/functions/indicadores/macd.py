import talib
from binance.client import Client as client_binance


# **Função para calcular MACD e identificar sinais**
def calculate_macd(df):
    macd, signal, hist = talib.MACD(
        df["close_price"], fastperiod=5, slowperiod=15, signalperiod=10
    )
    df["close_price"] = df["close_price"].astype(float)
    df["MACD"] = macd
    df["Signal"] = signal
    df["Histograma"] = hist

    # **Criar sinais de compra e venda**
    df["Buy_Signal"] = (df["MACD"] > df["Signal"]) & (
        df["MACD"].shift(1) <= df["Signal"].shift(1)
    )
    df["Sell_Signal"] = (df["MACD"] < df["Signal"]) & (
        df["MACD"].shift(1) >= df["Signal"].shift(1)
    )

    # Retorna os valores mais recentes
    return {
        "MACD": df["MACD"].iloc[-1],
        "Signal": df["Signal"].iloc[-1],
        "Histograma": df["Histograma"].iloc[-1],
        "LastHistograma": df["Histograma"].iloc[-2],
        "Buy_Signal": df["Buy_Signal"].iloc[-1],
        "Sell_Signal": df["Sell_Signal"].iloc[-1],
    }
