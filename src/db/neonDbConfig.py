import psycopg2
from psycopg2 import sql, extras
from datetime import datetime
import os

# String de conexão ao NeonDB
connection_string = os.getenv("NEON_DB_STRING_KEY")


def connect_to_db():
    """Conecta ao banco de dados e retorna a conexão."""
    try:
        conn = psycopg2.connect(connection_string)
        return conn
    except Exception as e:
        print(f"Erro ao conectar ao banco de dados: {e}")
        return None


def create_tables():
    """Cria as tabelas necessárias se elas não existirem."""
    conn = connect_to_db()
    if conn:
        with conn.cursor() as cur:
            try:

                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS account_balances (
                        id SERIAL PRIMARY KEY,
                        currency VARCHAR(50) NOT NULL,
                        balance NUMERIC NOT NULL,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );

                """
                )

                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS trade_logs (
                        id SERIAL PRIMARY KEY,
                        asset VARCHAR(50) NOT NULL,
                        quantity NUMERIC NOT NULL,
                        price NUMERIC NOT NULL,
                        order_type VARCHAR(10) NOT NULL,
                        status VARCHAR(10) NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );

                    ALTER TABLE trade_logs
                    ADD COLUMN balance NUMERIC NOT NULL DEFAULT 0;

                """
                )

                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS trade_states (
                       id SERIAL PRIMARY KEY,
                       asset VARCHAR(50) NOT NULL,
                       state BOOLEAN NOT NULL,  -- Tipo da coluna 'state' alterado para BOOLEAN
                       updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """
                )
                conn.commit()
                print("Tabelas criadas/verificadas com sucesso!")
            except Exception as e:
                print(f"Erro ao criar tabelas: {e}")
                conn.rollback()  # importante fazer rollback em caso de erro.
        conn.close()


def log_trade(asset, quantity, price, order_type, status, balance):
    """Insere um novo registro de negociação no banco de dados, incluindo o saldo."""
    conn = connect_to_db()
    if conn:
        with conn.cursor() as cur:
            try:
                cur.execute(
                    """
                    INSERT INTO trade_logs (asset, quantity, price, order_type, status, balance)
                    VALUES (%s, %s, %s, %s, %s, %s);
                """,
                    (asset, quantity, price, order_type, status, balance),
                )
                conn.commit()
                print("Log de negociação inserido com sucesso!")
            except Exception as e:
                print(f"Erro ao inserir log de negociação: {e}")
                conn.rollback()
        conn.close()


def calculate_profit_loss(last_balance, quantity, price, order_type):
    """Calcula o lucro ou perda baseado no tipo de ordem."""
    if order_type == "BUY":
        # Reduz o saldo pelo valor gasto
        new_balance = last_balance - (quantity * price)
    elif order_type == "SELL":
        # Aumenta o saldo pelo valor ganho
        new_balance = last_balance + (quantity * price)
    else:
        new_balance = last_balance

    return new_balance


def update_trade_state(asset, state):
    """Atualiza o estado da negociação (booleano) para um ativo específico."""
    conn = connect_to_db()
    if conn:
        with conn.cursor() as cur:
            try:
                # Verifica se já existe um estado para o ativo
                cur.execute("SELECT 1 FROM trade_states WHERE asset = %s", (asset,))
                exists = cur.fetchone()

                if exists:
                    # Se existe, atualiza o estado
                    cur.execute(
                        "UPDATE trade_states SET state = %s, updated_at = CURRENT_TIMESTAMP WHERE asset = %s",
                        (state, asset),
                    )
                else:
                    # Se não existe, insere um novo estado
                    cur.execute(
                        "INSERT INTO trade_states (asset, state) VALUES (%s, %s)",
                        (asset, state),
                    )

                conn.commit()
                print(
                    f"Estado de negociação para {asset} atualizado para {state} com sucesso!"
                )

            except Exception as e:
                print(f"Erro ao atualizar estado da negociação: {e}")
                conn.rollback()
        conn.close()


def get_last_trade_state(asset):
    """Recupera o último estado de negociação para um ativo específico."""
    conn = connect_to_db()

    if conn:
        with conn.cursor() as cur:
            try:
                cur.execute(
                    """
                    SELECT state FROM trade_states WHERE asset = %s ORDER BY updated_at DESC LIMIT 1;
                """,
                    (asset,),
                )

                result = cur.fetchone()
                conn.close()
                return (
                    result[0] if result else None
                )  # retorna None se não houver estado

            except Exception as e:
                print(f"Erro ao buscar o último estado de negociação: {e}")
                conn.close()
                return None
    else:
        return None


def update_account_balance(currency, balance):
    """Atualiza o saldo da conta para uma moeda específica."""
    conn = connect_to_db()
    if conn:
        with conn.cursor() as cur:
            try:
                # Verifica se já existe um saldo para a moeda
                cur.execute(
                    "SELECT 1 FROM account_balances WHERE currency = %s", (currency,)
                )
                exists = cur.fetchone()

                if exists:
                    # Se existe, atualiza o saldo
                    cur.execute(
                        "UPDATE account_balances SET balance = %s, updated_at = CURRENT_TIMESTAMP WHERE currency = %s",
                        (balance, currency),
                    )
                else:
                    # Se não existe, insere um novo saldo
                    cur.execute(
                        "INSERT INTO account_balances (currency, balance) VALUES (%s, %s)",
                        (currency, balance),
                    )

                conn.commit()
                print(
                    f"Saldo da conta para {currency} atualizado para {balance} com sucesso!"
                )

            except Exception as e:
                print(f"Erro ao atualizar saldo da conta: {e}")
                conn.rollback()
        conn.close()


def get_account_balance(currency):
    """Recupera o saldo atual da conta para uma moeda específica."""
    conn = connect_to_db()
    if conn:
        with conn.cursor() as cur:
            try:
                cur.execute(
                    "SELECT balance FROM account_balances WHERE currency = %s ORDER BY updated_at DESC LIMIT 1",
                    (currency,),
                )

                result = cur.fetchone()
                conn.close()
                return result[0] if result else None  # Retorna None se não houver saldo

            except Exception as e:
                print(f"Erro ao buscar saldo da conta: {e}")
                conn.close()
                return None
    else:
        return None
