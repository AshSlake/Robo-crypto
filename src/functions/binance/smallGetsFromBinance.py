def getLastStockAccountBalance(self):
    for stock in self.account_data["balances"]:
        if stock["asset"] == self.stock_code:
            return float(stock["free"])
    return 0.0


def printAllWallet(self):
    # Printa toda a carteira
    for stock in self.account_data["balances"]:
        if float(stock["free"]) > 0:
            print(stock)


def printStock(self):
    # Printa o ativo definido na classe
    for stock in self.account_data["balances"]:
        if stock["asset"] == self.stock_code:
            print(stock)


def printBrl(self):
    for stock in self.account_data["balances"]:
        if stock["asset"] == "BRL":
            print(stock)


def getUpdatedAccountData(self):
    return self.client_binance.get_account()


def getLastStockAccountBalance(self):
    for stock in self.account_data["balances"]:
        if stock["asset"] == self.stock_code:
            return float(stock["free"])
    return 0.0
