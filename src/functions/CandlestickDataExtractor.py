from decimal import Decimal
import pandas as pd
from binance.client import Client
from db.neonDbConfig import connect_to_db
from functions.logger import erro_logger
from psycopg2 import sql


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
            interval: Intervalo de tempo dos candlesticks (ex: Client.KLINE_INTERVAL_30MINUTE).
            limit: Número máximo de candlesticks a serem retornados (padrão: 500).
        """

        # Validação dos parâmetros
        if not symbol or not isinstance(symbol, str):
            raise ValueError("O símbolo fornecido é inválido.")
        if not (1 <= limit <= 1000):
            raise ValueError("O limite deve estar entre 1 e 1000.")

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
            self._klines = self.client.get_klines(
                symbol=self.symbol, interval=self.interval, limit=self.limit
            )
        except Exception as e:
            erro_logger.error(f"Erro ao buscar klines: {e}")
            return None

    def create_dataframe(self):
        """
        Cria um DataFrame do Pandas a partir dos dados brutos dos candlesticks (klines).
        Adiciona colunas extras para facilitar o acesso a informações importantes.
        """
        if self._klines is None:
            erro_logger.error(
                "Erro: Dados de klines não disponíveis. Chame fetch_klines() primeiro."
            )
            return

        try:
            columns = [
                "open_time",
                "open",
                "high",
                "low",
                "close",
                "volume",
                "close_time",
                "quote_asset_volume",
                "number_of_trades",
                "taker_buy_base_asset_volume",
                "taker_buy_quote_asset_volume",
                "ignore",
            ]

            self.df = pd.DataFrame(self._klines, columns=columns)

            # Converte as colunas relevantes para o tipo numérico (Decimal, de preferência)
            for col in [
                "open",
                "high",
                "low",
                "close",
                "volume",
                "quote_asset_volume",
                "taker_buy_base_asset_volume",
                "taker_buy_quote_asset_volume",
            ]:

                self.df[col] = pd.to_numeric(self.df[col])

            self.df["open_time"] = pd.to_datetime(self.df["open_time"], unit="ms")
            self.df["close_time"] = pd.to_datetime(self.df["close_time"], unit="ms")

        except Exception as e:
            erro_logger.error(f"Erro ao criar DataFrame: {e}")

    def get_candlestick_data(self):
        try:
            """
            Retorna os dados do candlestick como um DataFrame do Pandas.
            """

            if self.df is None:
                self.create_dataframe()  # Garante que o DataFrame já esteja criado
            return self.df
        except Exception as e:
            erro_logger.error(f"Erro ao retornar dados do candlestick: {e}")
            return None

    def get_latest_close_price(self):
        """
        Retorna o último preço de fechamento.
        """
        if self.df is not None:
            return self.df["close"].iloc[-1]
        return None

    def save_data_to_csv(self, filename: str):
        """
        Salva os dados do DataFrame em um arquivo CSV.
        """
        if self.df is not None:
            self.df.to_csv(filename, index=False)
            print(f"Dados salvos em {filename}")
        else:
            erro_logger.error("Erro: Não há dados para salvar.")

    def get_data_from_csv(self, filename: str):
        """
        Carrega dados de candlestick de um arquivo CSV.
        """
        try:
            self.df = pd.read_csv(filename)
            self.df["open_time"] = pd.to_datetime(self.df["open_time"])
            self.df["close_time"] = pd.to_datetime(self.df["close_time"])
            print(f"Dados carregados de {filename}")
        except Exception as e:
            erro_logger.error(f"Erro ao carregar dados de CSV: {e}")

    def save_candlestick_data_to_database(self, limit=1000):
        """
        Salva os dados de candlestick no banco de dados.

        Args:
         conn: Conexão com o banco de dados.
        """
        # Conexão com o banco de dados
        conn = None
        try:
            conn = connect_to_db()
            if self.df is None:
                erro_logger.error(
                    "Erro: Dados de candlestick não disponíveis para salvar."
                )
                return

            # Prepara o cursor para execução das queries
            with conn.cursor() as cursor:
                # Define o nome da tabela (ajuste conforme necessário)
                table_name = "candlestick_data"

                # Itera sobre os dados de candlestick e insere no banco de dados
                for _, row in self.df.iterrows():
                    insert_query = sql.SQL(
                        """
                    INSERT INTO {table_name} (symbol, open_time, open, high, low, close, volume, close_time)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    ).format(table_name=sql.Identifier(table_name))

                    # Parâmetros para a query
                data = (
                    self.symbol,
                    row["open_time"],
                    float(row["open"]),  # Decimal convertido para float
                    float(row["high"]),
                    float(row["low"]),
                    float(row["close"]),
                    float(row["volume"]),
                    row["close_time"],
                )

                # Executa a query de inserção
                cursor.execute(insert_query, data)

                # Antes de deletar registros antigos, conte o total de registros na tabela
                cursor.execute("SELECT COUNT(*) FROM candlestick_data;")
                count = cursor.fetchone()[0]

                # Se o número de registros ultrapassar o limite, deletar os mais antigos
                if count > limit:
                    cursor.execute(
                        """
                        DELETE FROM candlestick_data
                        WHERE id IN (
                        SELECT id FROM candlestick_data
                        ORDER BY open_time ASC
                        LIMIT %s
                        );
                        """,
                        (count - limit,),
                    )
            conn.commit()
            conn.close()  # Fecha a conexão com o banco de dados

            print(
                f"\n --------- \n Dados de candlestick salvos no banco de dados com sucesso!\n ---------\n"
            )

        except Exception as e:
            erro_logger.error(
                f"Erro ao salvar dados de candlestick no banco de dados: {e}"
            )
            if conn:
                conn.rollback()  # Rollback em caso de erro
        finally:
            if conn:
                conn.close()  # Fecha a conexão no final
