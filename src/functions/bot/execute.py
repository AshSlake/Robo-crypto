from datetime import datetime
import time
from estrategias.getMovingAverageVergenceRSI import getMovingAverageVergenceRSI
from functions.binance.getActualTradePositionForBinance import BinancePositionManager
from functions.bot.execute_trade import TradeExecutor
from functions.bot.updateAllData import UpdateAllData
from functions.get_current_price import get_current_price
from functions.logger import bot_logger, erro_logger
from binance.exceptions import BinanceAPIException, BinanceRequestException
from binance.enums import *
import traceback


class StockAccount:

    def execute(
        self,
        stock_code,
        OPERATION_CODE,
        BACKTESMODE,
        traded_quantity,
        candle_period,
    ):
        self.last_profit = None
        self.execute_trade = TradeExecutor()
        self.posicao_atual_ativo = BinancePositionManager
        self.updateAllData = UpdateAllData(
            stock_code=stock_code,
            operation_code=OPERATION_CODE,
            candle_period=candle_period,
        )
        self.account_data = None
        self.last_stock_account_balance = None
        self.actual_trade_position = None
        self.stock_data = None
        self.current_price_from_buy_order = 0

        try:
            results = self.updateAllData.updateAllData()
            self.account_data = results["account_data"]
            self.last_stock_account_balance = results["last_stock_account_balance"]
            self.actual_trade_position = results["actual_trade_position"]
            self.stock_data = results["stock_data"]

            message = (
                f"-----------------------------\n"
                f'Executado: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n'
                f'Posição atual: {"Comprado" if self.actual_trade_position else "Vendido"}\n'
                f"Balanço atual: {self.last_stock_account_balance} ({stock_code})\n"
                f"-----------------------------\n"
            )
            if self.last_profit is not None:
                message += f"Lucro da última venda: {self.last_profit:.8f} USDT\n"
            message += f"-----------------------------\n"
            print(message)
            bot_logger.info(message)

            # Cria uma instância da classe `estrategies`
            estrategia = getMovingAverageVergenceRSI(
                stock_data=self.stock_data,
                volume_threshold=1.5,
                rsi_period=5,
                rsi_upper=70,
                rsi_lower=30,
                stop_loss=0.05,
                stop_gain=0.10,
                operation_code=OPERATION_CODE,
                current_price_from_buy_order=self.current_price_from_buy_order,
            )

            ma_trade_decision = estrategia.getMovingAverageVergenceRSI(
                fast_window=7,
                slow_window=40,
                volatility_factor=0.3,
                initial_purchase_price=traded_quantity,
            )

            # Executa a ordem de compra/venda se a decisão da estratégia for verdadeira
            if ma_trade_decision is not None and BACKTESMODE is not True:
                if ma_trade_decision and not self.actual_trade_position:
                    self.execute_trade.execute_trade(SIDE_BUY, OPERATION_CODE)
                    self.actual_trade_position = (
                        self.posicao_atual_ativo.getActualTradePositionForBinance(
                            symbol=OPERATION_CODE, limit=1
                        )
                    )
                    self.current_price_from_buy_order = get_current_price(
                        symbol=OPERATION_CODE
                    )
                elif not ma_trade_decision and self.actual_trade_position:
                    self.execute_trade.execute_trade(SIDE_SELL, OPERATION_CODE)
                    self.actual_trade_position = (
                        self.posicao_atual_ativo.getActualTradePositionForBinance(
                            symbol=OPERATION_CODE, limit=1
                        )
                    )
        except BinanceRequestException as e:  # Captura erros de requisição da Binance
            erro_logger.error(f"Erro de requisição da Binance: {e}")
            bot_logger.warning("Tentando reconectar à Binance em 60 segundos...")
            time.sleep(60)  # Aguarda 60 segundos antes de tentar novamente
        except Exception as e:
            traceback.print_exc()  # Imprime o traceback do erro
            erro_logger.exception(
                f"Erro no Execute: {e},localização do erro: {traceback.format_exc()}"
            )
            print(f"Erro no Execute: {e},localização do erro: {traceback.format_exc()}")
