from locale import currency
import logging
from datetime import datetime
import os
from logging.handlers import RotatingFileHandler

# Cria o diretório 'logs' se ele não existir
log_dir = 'logs'  # Diretório relativo ao script
os.makedirs(log_dir, exist_ok=True)

# Logger para erros
erro_logger = logging.getLogger('erros')
erro_logger.setLevel(logging.ERROR)
erro_handler = RotatingFileHandler(os.path.join(log_dir, 'erros.log'), maxBytes=5 * 1024 * 1024, backupCount=5)
erro_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
erro_handler.setFormatter(erro_formatter)
erro_logger.addHandler(erro_handler)

# Logger para trades/ordens
trade_logger = logging.getLogger('trades')
trade_logger.setLevel(logging.INFO)
trade_handler = RotatingFileHandler(os.path.join(log_dir, 'trades.log'), maxBytes=10 * 1024 * 1024, backupCount=3)
trade_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
trade_handler.setFormatter(trade_formatter)
trade_logger.addHandler(trade_handler)

# Logger para mensagens gerais do bot
bot_logger = logging.getLogger('bot')
bot_logger.setLevel(logging.INFO)
bot_handler = RotatingFileHandler(os.path.join(log_dir, 'bot.log'), maxBytes=5 * 1024 * 1024, backupCount=5)
bot_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
bot_handler.setFormatter(bot_formatter)
bot_logger.addHandler(bot_handler)

def createLogOrder(order):
  try:
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

  except Exception as e:
    erro_logger.exception(f"Erro ao registrar ordem: {e}")