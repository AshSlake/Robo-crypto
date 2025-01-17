import requests


class BinanceTopGainers:
    def __init__(self):
        self.url = "https://api.binance.com/api/v3/ticker/24hr"

    def fetch_tickers(self):
        try:
            response = requests.get(self.url)
            if response.status_code == 200:
                all_tickers = response.json()
                return all_tickers
            else:
                print(f"Erro na API Binance: {response.status_code}")
                return None
        except requests.RequestException as e:
            print(f"Erro ao acessar a API Binance: {e}")
            return None

    def get_top_50_gainers(self):
        all_tickers = self.fetch_tickers()
        if all_tickers:
            top_50 = sorted(
                all_tickers, key=lambda x: float(x["priceChangePercent"]), reverse=True
            )[:50]
            return top_50
        return []

    def display_top_50(self):
        top_50 = self.get_top_50_gainers()
        if top_50:
            for ticker in top_50:
                print(
                    f"Par: {ticker['symbol']}, Mudança %: {ticker['priceChangePercent']}"
                )


# Uso da classe
if __name__ == "__main__":
    binance_top_gainers = BinanceTopGainers()
    binance_top_gainers.display_top_50()
