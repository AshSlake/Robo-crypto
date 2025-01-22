from decimal import Decimal
import logging
from datetime import datetime
import os
from logging.handlers import TimedRotatingFileHandler
from binance.enums import SIDE_BUY
from db.neonDbConfig import (
    calculate_profit_loss,
    get_account_balance,
    log_trade,
    update_account_balance,
    update_trade_state,
)

# Configuração do diretório de logs principal
log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)

# Subdiretórios para cada tipo de log
error_log_dir = os.path.join(log_dir, "erros")
trade_log_dir = os.path.join(log_dir, "trades")
bot_log_dir = os.path.join(log_dir, "bot")

# Criar subdiretórios se não existirem
os.makedirs(error_log_dir, exist_ok=True)
os.makedirs(trade_log_dir, exist_ok=True)
os.makedirs(bot_log_dir, exist_ok=True)

# Logger para erros
erro_logger = logging.getLogger("erros")
erro_logger.setLevel(logging.ERROR)
erro_handler = TimedRotatingFileHandler(
    os.path.join(error_log_dir, "erros.log"), when="midnight", interval=1, backupCount=7
)
erro_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
erro_handler.setFormatter(erro_formatter)
erro_logger.addHandler(erro_handler)

# Logger para trades/ordens
trade_logger = logging.getLogger("trades")
trade_logger.setLevel(logging.INFO)
trade_handler = TimedRotatingFileHandler(
    os.path.join(trade_log_dir, "trades.log"),
    when="midnight",
    interval=1,
    backupCount=7,
)
trade_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
trade_handler.setFormatter(trade_formatter)
trade_logger.addHandler(trade_handler)

# Logger para mensagens gerais do bot
bot_logger = logging.getLogger("bot")
bot_logger.setLevel(logging.INFO)
bot_handler = TimedRotatingFileHandler(
    os.path.join(bot_log_dir, "bot.log"), when="midnight", interval=1, backupCount=7
)
bot_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
bot_handler.setFormatter(bot_formatter)
bot_logger.addHandler(bot_handler)


def createLogOrder(order):
    try:
        # Extraindo as informações necessárias
        side = order["side"]
        stock_code = "SOL"
        type = order["type"]
        quantity = float(order["executedQty"])
        asset = order["symbol"]
        price_per_unit = float(order["fills"][0]["price"])
        currency = order["cummulativeQuoteQty"]
        timestamp = order["transactTime"]
        total_value = float(order["cummulativeQuoteQty"])

        datetime_transact = datetime.utcfromtimestamp(timestamp / 1000).strftime(
            "%H:%M:%S - %Y-%m-%d"
        )

        # Recuperar o último saldo conhecido
        last_balance = get_account_balance(currency)

        if last_balance is None:
            last_balance = 0.0  # Ou outro valor padrão apropriado.

        # Calcular o novo saldo
        new_balance = calculate_profit_loss(
            last_balance, quantity, price_per_unit, side
        )

        # Atualizar o saldo no banco de dados
        update_account_balance(currency, new_balance)

        # Criando as mensagens para log
        log_message = (
            "\n  ____________________________________________\n"
            "ORDEM EXECUTADA:\n"
            f"Side: {side}\n"
            f"Ativo: {asset}\n"
            f"Quantidade: {quantity:.4f}\n"
            f"Valor no momento: {price_per_unit:.2f}\n"
            f"Moeda: {currency}\n"
            f"Valor em {currency}: {total_value:.2f}\n"
            f"Type: {type}\n"
            f"Data/Hora: {datetime_transact}\n"
            "Complete order:\n"
            f"{order}"
            "\n  ____________________________________________\n"
        )

        # Exibindo no console e gravando logs
        print(log_message)
        bot_logger.info(log_message)
        trade_logger.info(log_message)

        # --- Integração com o banco de dados ---
        log_trade(
            asset=order["symbol"],
            quantity=float(order["executedQty"]),
            price=float(order["fills"][0]["price"]),
            order_type=order["side"],  # SIDE_BUY ou SIDE_SELL
            status=order["status"],  # ex: "FILLED"
            balance=new_balance,  # Novo saldo calculado
        )

        if (
            order["status"] == "FILLED" or order["status"] == "PARTIALLY_FILLED"
        ):  # Lógica para ambos os status
            update_trade_state(
                stock_code, order["side"] == SIDE_BUY
            )  # True se comprou, False se vendeu

    except Exception as e:
        erro_logger.exception(f"Erro ao registrar ordem: {e}")

    except Exception as e:
        erro_logger.exception(f"Erro ao registrar ordem: {e}")


# Fechar handlers ao final da execução para liberar recursos
logging.shutdown()
