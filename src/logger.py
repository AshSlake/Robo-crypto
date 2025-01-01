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
    type = order['type']
    quantity = order['executedQty']

    # Ajuste para o caso em que existe mais de uma transação em uma única ordem
    price_per_unit = order['fills'][0]['price'] 
    asset = order['fills'][0]['commissionAsset']

    total_value = order['cummulativeQuoteQty']
    timestamp = order['transactTime']
    datetime_transact = datetime.utcfromtimestamp(timestamp / 1000).strftime('%H:%M:%S - %Y-%m-%d')

    # Criando as mensagens para log
    log_message = (
        "ORDEM EXECUTADA:\n"
        f"Side: {order['side']}\n"
        f"Ativo: {asset}\n"
        f"Quantidade: {quantity}\n"
        f"Valor no momento: {price_per_unit}\n"
        f"Moeda: {order['fills'][0]['currency']}\n"
        f"Valor em {order['fills'][0]['currency']}: {total_value}\n"
        f"Type: {type}\n"
        f"Data/Hora: {datetime_transact}\n"
        "Complete order:\n"
        f"{order}"
    )

    # Criando as mensagens para print
    print_message = (
        "ORDEM EXECUTADA:\n"
        f"Side: {order['side']}\n"
        f"Ativo: {asset}\n"
        f"Quantidade: {quantity}\n"
        f"Valor no momento: {price_per_unit}\n"
        f"Moeda: {order['fills'][0]['currency']}\n"
        f"Valor em {order['fills'][0]['currency']}: {total_value}\n"
        f"Type: {type}\n"
        f"Data/Hora: {datetime_transact}\n"
        f"Complete order:\n"
        f"{order}"
    )

    # Exibindo no console
    print(print_message)
    # Registrando no log
    logging.info(log_message)