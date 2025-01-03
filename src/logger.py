from locale import currency
import logging
from datetime import datetime


# Configura o logger
logging.basicConfig(
    filename='src/logs/trading_bot.log', 
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def createLogOrder(order):
    # Extraindo as informações necessárias
    side = order['side']
    type = order['type']
    quantity = order['executedQty']
    asset = order['symbol']
    price_per_unit = order['fills'][0]['price'] 
    currency = order['cummulativeQuoteQty']
    timestamp = order['transactTime'] 
    total_value = order['cummulativeQuoteQty']
  
    datetime_transact = datetime.utcfromtimestamp(timestamp / 1000).strftime('%H:%M:%S - %Y-%m-%d')

    # Criando as mensagens para log
    log_message = (
        "\n  ____________________________________________\n"
        "ORDEM EXECUTADA:\n"
        f"Side: {side}\n"
        f"Ativo: {asset}\n"
        f"Quantidade: {quantity}\n"
        f"Valor no momento: {price_per_unit}\n"
        f"Moeda: {currency}\n"
        f"Valor em {currency}: {total_value}\n"
        f"Type: {type}\n"
        f"Data/Hora: {datetime_transact}\n"
        "Complete order:\n"
        f"{order}"
        "\n  ____________________________________________\n"
    )

    # Criando as mensagens para print
    print_message = (
        "\n  ____________________________________________\n"
        "ORDEM EXECUTADA:\n"
        f"Side: {side}\n"
        f"Ativo: {asset}\n"
        f"Quantidade: {quantity}\n"
        f"Valor no momento: {price_per_unit}\n"
        f"Moeda: {currency}\n"
        f"Valor em {currency}: {total_value}\n"
        f"Type: {type}\n"
        f"Data/Hora: {datetime_transact}\n"
        f"Complete order:\n"
        f"{order}"
        "\n  ____________________________________________\n"
    )

    # Exibindo no console
    print(print_message)
    # Registrando no log
    logging.info(log_message)