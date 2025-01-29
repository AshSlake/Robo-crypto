import os
import talib
import pandas as pd
import numpy as np
from binance.client import Client as client_binance

# **Configurar a API da Binance**
api_key = os.getenv("BINANCE_API_KEY")
secret_key = os.getenv("BINANCE_SECRET_KEY")
client_binance = client_binance(api_key, secret_key)


# **Função para obter dados históricos do ativo**
def get_historical_data(symbol, interval, limit):
    klines = client_binance.get_klines(symbol=symbol, interval=interval, limit=limit)
    df = pd.DataFrame(
        klines,
        columns=[
            "timestamp",
            "open",
            "high",
            "low",
            "close",
            "volume",
            "close_time",
            "quote_asset_volume",
            "number_of_trades",
            "taker_buy_base_vol",
            "taker_buy_quote_vol",
            "ignore",
        ],
    )
    df["timestamp"] = (
        pd.to_datetime(
            df["timestamp"], unit="ms"
        )  # Converte de milissegundos para datetime
        .dt.tz_localize("UTC")  # Define o fuso horário como UTC
        .dt.tz_convert("America/Sao_Paulo")  # Converte para o fuso horário de São Paulo
    )
    df["close"] = df["close"].astype(float)  # Converte o preço de fechamento para float

    return df[["timestamp", "close"]]


# **Função para calcular MACD e identificar sinais**
def calculate_macd(df):
    macd, signal, hist = talib.MACD(
        df["close"], fastperiod=14, slowperiod=20, signalperiod=10
    )
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
        "Buy_Signal": df["Buy_Signal"].iloc[-1],
        "Sell_Signal": df["Sell_Signal"].iloc[-1],
    }


# EXEMPLO: Utilizar o ativo SOLUSDT (Solana) com intervalo de 15 minutos e limite de 500 candlesticks
# **Executar o código**
df = get_historical_data(symbol="SOLUSDT", interval="15m", limit=500)
macd_values = calculate_macd(df)

# **Exibir os resultados**
print("\n📊 Indicador MACD:")
print(f"MACD: {macd_values['MACD']:.5f}")
print(f"Linha de Sinal: {macd_values['Signal']:.5f}")
print(f"Histograma: {macd_values['Histograma']:.5f}")
print(f"Sinal de Compra: {macd_values['Buy_Signal']}")
print(f"Sinal de Venda: {macd_values['Sell_Signal']}")
