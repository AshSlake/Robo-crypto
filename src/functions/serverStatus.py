import requests


def check_binance_status():
    url = "https://api.binance.com/sapi/v1/system/status"
    try:
        response = requests.get(url)
        response.raise_for_status()  # Levanta um erro se o status da resposta for 4xx ou 5xx
        data = response.json()

        if data.get("status") == 0:
            return "Sistema operacional normal"
        elif data.get("status") == 1:
            return "Sistema em manutenção"
        else:
            return f"Resposta inesperada: {data}"
    except requests.exceptions.RequestException as e:
        return f"Erro ao acessar a API da Binance: {e}"


# Exemplo de uso
if __name__ == "__main__":
    print(check_binance_status())
