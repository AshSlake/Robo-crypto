def init_bot(self, total_free, min_balance):
    """
    Inicializa o bot com valores essenciais.

    Args:
        total_free (float): Taxa total aplicada às transações (compra + venda).
        min_balance (float): Saldo mínimo necessário para considerar que há uma posição ativa.
    """
    self.total_free = total_free
    self.min_balance = min_balance


def calculate_profit_levels(self):
    """
    Calcula níveis de lucro (profit levels) com base no preço de compra e as taxas definidas.

    Returns:
        tuple: Um dicionário contendo os níveis de lucro e o lucro atual (em porcentagem).
    """
    try:
        # Definir taxa total (compra + venda)
        total_fee = self.total_free  # Ex.: 0.0015 = 0.15% total

        # Obter o preço atual do ativo
        ticker = self.client_binance.get_symbol_ticker(symbol=self.operation_code)
        current_price = float(ticker["price"])

        # Calcular níveis de lucro
        profit_levels = {
            "main": {
                "percentage": self.profit_percentage,
                "price": self.last_buy_price * (1 + (self.profit_percentage / 100)),
                "description": "Meta principal",
            },
            "level_1": {
                "percentage": self.profit_level_1,
                "price": self.last_buy_price * (1 + (self.profit_level_1 / 100)),
                "description": f"Nível 1 ({self.profit_level_1}%)",
            },
            "level_2": {
                "percentage": self.profit_level_2,
                "price": self.last_buy_price * (1 + (self.profit_level_2 / 100)),
                "description": f"Nível 2 ({self.profit_level_2}%)",
            },
            "break_even": {
                "percentage": total_fee * 100,
                "price": self.last_buy_price * (1 + total_fee),
                "description": "Break-even (sem lucro, sem prejuízo)",
            },
        }

        # Calcular lucro atual em porcentagem
        current_profit = (
            (current_price - self.last_buy_price) / self.last_buy_price
        ) * 100

        # Exibir informações detalhadas
        self._display_profit_levels(profit_levels, current_price, current_profit)

        return profit_levels, current_profit

    except Exception as e:
        print(f"Erro ao calcular níveis de lucro: {str(e)}")
        return None, None


def _display_profit_levels(self, profit_levels, current_price, current_profit):
    """
    Exibe informações sobre os níveis de lucro e a situação atual.

    Args:
        profit_levels (dict): Dicionário contendo os níveis de lucro calculados.
        current_price (float): Preço atual do ativo.
        current_profit (float): Lucro atual em porcentagem.
    """
    print("\n=== NÍVEIS DE TAKE PROFIT ===")
    print(f"Preço de Entrada: {self.last_buy_price:.8f}")
    print(f"Preço Atual: {current_price:.8f}")
    print(f"Lucro Atual: {current_profit:.2f}%")

    for level, data in profit_levels.items():
        print(f"\n{data['description']}:")
        print(f"- Alvo: {data['percentage']:.2f}%")
        print(f"- Preço: {data['price']:.8f}")
        if current_price < data["price"]:
            print(
                f"- Falta: {(data['price'] - current_price):.8f} "
                f"({(data['percentage'] - current_profit):.2f}%)"
            )


def checkProfitSell(self, profit_percentage):
    """
    Verifica se a meta de lucro foi atingida e decide pela venda.

    Args:
        profit_percentage (float): Porcentagem de lucro alvo para venda.

    Returns:
        bool: Verdadeiro se a venda deve ser realizada, Falso caso contrário.
    """
    try:
        # Validar saldo
        balance = self.client_binance.get_asset_balance(asset=self.stock_code)
        available_balance = float(balance["free"])

        if available_balance < self.min_balance:
            self.actual_trade_position = False
            print(
                f"Saldo muito baixo ({available_balance:.8f} {self.stock_code}), "
                f"considerando como sem posição"
            )
            return False

        # Obter preço atual e ordens
        ticker = self.client_binance.get_symbol_ticker(symbol=self.operation_code)
        current_price = float(ticker["price"])
        orders = self.client_binance.get_all_orders(
            symbol=self.operation_code, limit=10
        )

        # Encontrar última ordem de compra
        last_buy = next(
            (
                order
                for order in orders
                if order["side"] == "BUY" and order["status"] == "FILLED"
            ),
            None,
        )

        if not last_buy:
            print("Nenhuma ordem de compra encontrada.")
            return False

        buy_price = float(last_buy["price"])
        current_profit_percentage = ((current_price - buy_price) / buy_price) * 100

        # Calcular níveis de lucro
        profit_levels, _ = self.calculate_profit_levels()

        # Exibir análise de lucro
        print("\n=== ANÁLISE DE LUCRO ===")
        print(f"Preço de Compra: {buy_price:.8f}")
        print(f"Preço Atual: {current_price:.8f}")
        print(f"Lucro Atual: {current_profit_percentage:.2f}%")

        # Verificar meta principal
        if current_profit_percentage >= profit_percentage:
            print(f"\n🎯 Meta principal de {profit_percentage}% atingida!")
            return True

        # Verificar níveis de lucro adicionais
        for level in ["level_1", "level_2"]:
            if current_profit_percentage >= profit_levels[level]["percentage"]:
                volume_ratio = _calculate_volume_ratio()
                if volume_ratio < getattr(self, f"min_volume_ratio_{level[-1]}"):
                    print(
                        f"\n📉 {profit_levels[level]['description']} atingido com volume fraco "
                        f"(ratio: {volume_ratio:.2f})"
                    )
                    return True

        print("\nDecisão: Manter posição")
        return False

    except Exception as e:
        print(f"Erro ao verificar lucro: {str(e)}")
        return False


def _calculate_volume_ratio(self):
    """
    Calcula o volume ratio com base no volume atual e na média móvel de 20 períodos.

    Returns:
        float: Ratio do volume atual para a média móvel.
    """
    return (
        self.stock_data["volume"].iloc[-1]
        / self.stock_data["volume"].rolling(window=20).mean().iloc[-1]
    )
