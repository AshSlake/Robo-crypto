import requests
import decimal


def get_current_price(symbol):
    """
    Obtém o preço atual de um símbolo na Binance.

    Args:
        symbol (str): O símbolo do par de mercado (exemplo: 'BTCUSDT').

    Returns:
        Decimal: O preço atual do ativo como Decimal.
    """
    try:
        # Endpoint da API pública da Binance para obter preços
        url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"

        # Faz a requisição GET
        response = requests.get(url)
        response.raise_for_status()  # Levanta exceções para erros HTTP

        # Obtém o preço do JSON retornado
        data = response.json()
        current_price = decimal.Decimal(data["price"])

        print(f"Preço atual de {symbol}: {current_price:.2f}")
        return current_price

    except requests.exceptions.RequestException as e:
        print(f"Erro ao obter o preço atual de {symbol}: {e}")
        return None

    except KeyError:
        print(f"Erro ao processar a resposta da API para {symbol}.")
        return None
