from functions.logger import erro_logger


def updateAllData(self):
    try:
        self.account_data = self.getUpdatedAccountData()
        self.last_stock_account_balance = self.getLastStockAccountBalance()
        self.actual_trade_position = self.getActualTradePositionForBinance()
        self.stock_data = self.getStockData()
    except Exception as e:
        erro_logger.exception(
            f"------------------------------------\nErro ao atualizar dados: {e}"
        )
        erro_logger.exception(f"------------------------------------\n")
