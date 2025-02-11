import os
import time
from dotenv import load_dotenv
from binance.client import Client
from binance.enums import *
from binance.exceptions import BinanceAPIException, BinanceRequestException
import psycopg2
from db.neonDbConfig import create_tables
from functions.bot.execute import StockAccount
from functions.calculators.calculate_max_buy_sell_quantity import QuantityCalculator
from functions.logger import bot_logger, erro_logger
import traceback

from functions.serverStatus import CheckBinanceStatus


# Load environment variables
load_dotenv()
api_key = os.getenv("BINANCE_API_KEY")
secret_key = os.getenv("BINANCE_SECRET_KEY")

# CONFIGURAÇÔES DO BOT
STOCK_CODE = "SOL"  # Código do ativo negociado
OPERATION_CODE = (
    "SOLUSDT"  # Código da operação no formato de par de moedas (ex: "SOLUSDT")
)
CANDLE_PERIOD = (
    Client.KLINE_INTERVAL_30MINUTE
)  # Período dos candles para análise (ex: Client.KLINE_INTERVAL_30MINUTE)
TRADED_QUANTITY = 0.090  # Quantidade do ativo a ser negociada (ex: 0.090)
BACKTESMODE = True  # Modo de backtest (True para simulação, False para operações reais)
TIME_SLEEP = 60  # Tempo de espera entre cada iteração do loop principal (em segundos)


class BinanceTraderBot:
    """
    Classe responsável por automatizar operações de trading na plataforma Binance.

    Atributos:
        last_trade_decision (bool): Última decisão de trading (True para compra, False para venda).
        last_profit (float): Último lucro obtido em uma operação.
        stock_code (str): Código do ativo negociado (ex: "SOL").
        operation_code (str): Código da operação no formato de par de moedas (ex: "SOLUSDT").
        traded_quantity (float): Quantidade do ativo a ser negociada.
        entry_price (float): Preço de entrada da última operação.
        purchased_quantity (float): Quantidade do ativo comprada na última operação.
        traded_percentage (float): Porcentagem do saldo da conta utilizada em cada operação.
        candle_period (str): Período dos candles para análise (ex: "30m").
        execute (StockAccount): Instância da classe StockAccount para executar operações.
        current_price_from_buy_order (float): Preço atual do ativo desde a última ordem de compra.
    """

    last_trade_decision: bool = False
    last_profit = None

    def __init__(
        self,
        stock_code,
        operation_code,
        traded_quantity,
        traded_percentage,
        candle_period,
    ):
        """
        Inicializa o bot com as configurações fornecidas.

        Args:
            stock_code (str): Código do ativo a ser negociado.
            operation_code (str): Código da operação no formato de par de moedas.
            traded_quantity (float): Quantidade do ativo a ser negociada.
            traded_percentage (float): Porcentagem do saldo da conta a ser utilizada.
            candle_period (str): Período dos candles para análise.
        """
        # variaveis iniciais
        self.stock_code = stock_code
        self.operation_code = operation_code
        self.traded_quantity = traded_quantity
        self.entry_price = 0.0
        self.purchased_quantity = 0.0
        self.traded_percentage = traded_percentage
        self.candle_period = candle_period
        self.execute = StockAccount()
        self.current_price_from_buy_order = 0
        print("Robo Trader iniciado...")
        bot_logger.info("Robo Trader iniciado...")

    def iniciar_bot(self):
        """
        Inicia a execução do bot. Chama a função `execute` da instância `StockAccount`
        para realizar operações de trading.

        Captura e exibe erros que ocorrem durante a execução, incluindo o traceback
        para facilitar a depuração.
        """
        try:
            status_api_binance = CheckBinanceStatus.check_binance_status()
            # Executa as operações de trading
            self.execute.execute(
                self.stock_code,
                OPERATION_CODE,
                BACKTESMODE,
                self.traded_quantity,
                CANDLE_PERIOD,
            )
        except Exception as e:
            # Captura o traceback como uma string
            traceback_info = traceback.format_exc()
            # Exibe a mensagem de erro e o traceback
            print(f"Erro ao iniciar o bot: {e}\nLocalização do erro:\n{traceback_info}")
        except BinanceRequestException as e:
            erro_logger.exception(f"Erro de requisição da Binance: {e}")
            print(f"Erro de requisição da Binance: {e}")
        except status_api_binance is False:
            print(f"Servidor fora da API do AR!")
            erro_logger.exception(f"Servidor fora da API do AR!")
            time.sleep(60)


# Cria as tabelas do banco de dados
try:
    create_tables()
except Exception as e:
    traceback_info = traceback.format_exc()
    print(
        f"Erro ao conectar ao banco de dados: {e}\nLocalização do erro:\n{traceback_info}"
    )
except psycopg2.OperationalError as e:
    print(f"Erro ao conectar ao banco de dados: {e}")
except BinanceRequestException as e:
    erro_logger.exception(f"Erro de requisição da Binance: {e}")
    print(f"Erro de requisição da Binance: {e}")

# instancia o bot
TraderBot = BinanceTraderBot(
    STOCK_CODE, OPERATION_CODE, TRADED_QUANTITY, 100, CANDLE_PERIOD
)

# Loop principal para iniciar a execução do bot
while True:
    TraderBot.iniciar_bot()
    time.sleep(TIME_SLEEP)
