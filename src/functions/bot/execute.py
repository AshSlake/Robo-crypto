from datetime import datetime
import time
from estrategias.getMovingAverageVergenceRSI import getMovingAverageVergenceRSI
from functions.logger import bot_logger, erro_logger
from binance.exceptions import BinanceAPIException, BinanceRequestException


def execute(
    self,
    OPERATION_CODE,
    BACKTESMODE,
    SIDE_BUY,
    SIDE_SELL,
    actual_trade_position,
    last_stock_account_balance,
):

    try:
        self.updateAllData()
        # Obtém dados do símbolo
        print(f"\n-----------------------------")
        print(
            f'Executado: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'
        )  # Adiciona o horário atual
        print(f'Posição atual: {"Comprado" if actual_trade_position else "Vendido" }')
        print(f"Balanço atual: {last_stock_account_balance} ({self.stock_code})")
        if self.last_profit is not None:  # Exibe apenas se houver lucro registrado.
            print(f"Lucro da última venda: {self.last_profit:.8f} USDT")
        print(f"-----------------------------\n")

        message = (
            f"-----------------------------\n"
            f'Executado: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n'
            f'Posição atual: {"Comprado" if self.actual_trade_position else "Vendido"}\n'
            f"Balanço atual: {self.last_stock_account_balance} ({self.stock_code})\n"
            f"-----------------------------\n"
        )
        if self.last_profit is not None:
            message += f"Lucro da última venda: {self.last_profit:.8f} USDT\n"
        message += f"-----------------------------\n"
        bot_logger.info(message)

        # Usa getActualTradePositionForBinance para obter a posição atual do trade
        self.actual_trade_position = self.getActualTradePositionForBinance()

        # Cria uma instância da classe `estrategies`
        estrategias = getMovingAverageVergenceRSI.getMovingAverageVergenceRSI(
            stock_data=self.stock_data,
            operation_code=OPERATION_CODE,  # Passa o código da operação
            actual_trade_position=self.actual_trade_position,
        )

        ma_trade_decision = estrategias.getMovingAverageVergenceRSI(
            fast_window=7,
            slow_window=40,
            volatility_factor=0.3,
            initial_purchase_price=self.traded_quantity,
        )

        # Executa a ordem de compra/venda se a decisão da estratégia for verdadeira
        if ma_trade_decision is not None and BACKTESMODE is not True:
            if ma_trade_decision and not self.actual_trade_position:
                self.execute_trade(SIDE_BUY)
                self.actual_trade_position = (
                    self.getActualTradePositionForBinance()
                )  # ou True, se tiver certeza da compra
            elif not ma_trade_decision and self.actual_trade_position:
                self.execute_trade(SIDE_SELL)
                self.actual_trade_position = (
                    self.getActualTradePositionForBinance()
                )  # ou False, se tiver certeza da venda

    except BinanceRequestException as e:  # Captura erros de requisição da Binance
        erro_logger.error(f"Erro de requisição da Binance: {e}")
        bot_logger.warning("Tentando reconectar à Binance em 60 segundos...")
        time.sleep(60)  # Aguarda 60 segundos antes de tentar novamente
