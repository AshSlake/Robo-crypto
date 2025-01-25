def get_balance(self):
    account_info = self.client_binance.get_account()
    for asset in account_info["balances"]:
        if asset["asset"] == "USDT":
            return float(asset["free"])
    return 0.0
