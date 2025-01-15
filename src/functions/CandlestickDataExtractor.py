import pandas as pd
from binance.client import Client
from logger import erro_logger

class CandlestickDataExtractor:
    """
    Extrai e processa dados de candlestick (OHLCV) da Binance.
    """

    def __init__(self, client: Client, symbol: str, interval: str, limit: int = 500):
        """
        Inicializa o extrator de dados.

        Args:
            client: Instância do cliente Binance.
            symbol: Símbolo do par de trading (ex: 'BTCUSDT').
            interval: Intervalo de tempo dos candlesticks (ex: Client.KLINE_INTERVAL_15MINUTE).
            limit: Número máximo de candlesticks a serem retornados (padrão: 500).
        """
        self.client = client
        self.symbol = symbol
        self.interval = interval
        self.limit = limit
        self._klines = None  # Armazena os dados brutos dos candlesticks (klines)
        self.df = None  # Armazena os dados em um DataFrame do Pandas

    def fetch_klines(self):
        """
        Busca os dados de candlestick (klines) da Binance API.
        """
        try:
            self._klines = self.client.get_klines(symbol=self.symbol, interval=self.interval, limit=self.limit)
        except Exception as e:
            erro_logger.error(f"Erro ao buscar klines: {e}")
            return None

    def create_dataframe(self):
        """
        Cria um DataFrame do Pandas a partir dos dados brutos dos candlesticks (klines).
        Adiciona colunas extras para facilitar o acesso a informações importantes.
        """
        if self._klines is None:
            erro_logger.error("Erro: Dados de klines não disponíveis. Chame fetch_klines() primeiro.")
            return

        try:
            columns = [
                'open_time', 'open', 'high', 'low', 'close', 'volume', 'close_time',
                'quote_asset_volume', 'number_of_trades', 'taker_buy_base_asset_volume',
                'taker_buy_quote_asset_volume', 'ignore'
            ]

            self.df = pd.DataFrame(self._klines, columns=columns)

            # Converte as colunas relevantes para o tipo numérico (Decimal, de preferência)
            for col in ['open', 'high', 'low', 'close', 'volume', 'quote_asset_volume',
                        'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume']:

                self.df[col] = pd.to_numeric(self.df[col])

            self.df['open_time'] = pd.to_datetime(self.df['open_time'], unit='ms')
            self.df['close_time'] = pd.to_datetime(self.df['close_time'], unit='ms')

        except Exception as e:
            erro_logger.error(f"Erro ao criar DataFrame: {e}")



    def get_candlestick_data(self):
      try:
        """
        Retorna os dados do candlestick como um DataFrame do Pandas.
        """

        if self.df is None:
            self.create_dataframe() # Garante que o DataFrame já esteja criado
        return self.df
      except Exception as e:
          erro_logger.error(f"Erro ao retornar dados do candlestick: {e}")
          return None