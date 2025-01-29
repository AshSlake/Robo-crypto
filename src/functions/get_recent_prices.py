from functions.CandlestickDataExtractor import CandlestickDataExtractor


def get_recent_prices(self, symbol, interval, limit=1000):
    """
    Obtém os dados de preços recentes do mercado a partir do DataFrame gerado por CandlestickDataExtractor.

    Args:
        symbol (str): O símbolo do par de mercado (exemplo: 'BTCUSDT').
        interval (str): O intervalo de tempo para os candlesticks (exemplo: '15m').
        limit (int): Número máximo de registros a serem extraídos.

    Returns:
        list: Uma lista de preços de fechamento recentes.
    """
    # Instanciar o CandlestickDataExtractor com os parâmetros fornecidos
    data_extractor = CandlestickDataExtractor(
        self.client_binance,
        symbol=symbol,
        interval=interval,
        limit=limit,
    )

    # Extraia os dados e crie o DataFrame
    data_extractor.fetch_klines()
    data_extractor.create_dataframe()

    if data_extractor.df is not None:
        # Salvar os dados no banco de dados (opcional)
        data_extractor.save_candlestick_data_to_database(limit=1000)

        # Retornar os preços de fechamento como uma lista
        recent_prices = data_extractor.df["close"].tolist()
        recent_volumes = data_extractor.df["volume"].tolist()
        return recent_prices, recent_volumes
    else:
        print(f"Não foi possível recuperar os dados de {symbol}.")
        return []
