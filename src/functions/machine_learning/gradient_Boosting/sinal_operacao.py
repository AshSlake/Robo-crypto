def gerar_sinal_janela_deslizante_ultimo(
    predicoes, tamanho_janela, limiar_compra, limiar_venda, horizonte_maximo=60
):
    """
    Gera um sinal de trading com base na última janela deslizante, considerando apenas as previsões
    dentro de um horizonte máximo.

    Args:
      predicoes: Lista de previsões (-1, 0, 1).

      tamanho_janela: O número de previsões que você quer usar para tomar uma decisão
      Uma janela maior suaviza o sinal, enquanto uma janela menor reage mais rapidamente às mudanças.

      limiar_compra: Um valor limite. Se a soma das previsões na janela for maior que esse valor, a função gera um sinal de compra.

      limiar_venda: Outro valor limite. Se a soma das previsões na janela for menor que esse valor, a função gera um sinal de venda.

      horizonte_maximo: O número máximo de previsões a serem consideradas, a partir da previsão mais recente
      Isso permite que você ignore previsões de longo prazo (que podem ser menos precisas).

    Returns:
      Sinal de trading ("compra", "venda" ou "manter") ou None se não houver dados suficientes.
    """

    horizonte_maximo = int(horizonte_maximo)  # Converte para inteiro
    if horizonte_maximo <= 0:
        print("Erro: horizonte_maximo deve ser maior que zero.")
        return None

    # Limita as previsões ao horizonte máximo
    horizonte_maximo = min(horizonte_maximo, len(predicoes))
    predicoes_limitadas = predicoes[:horizonte_maximo]

    if len(predicoes_limitadas) < tamanho_janela:
        print(
            f"Erro: Não há dados suficientes para gerar um sinal de trading. Temos {len(predicoes_limitadas)} previsões, mas precisamos de {tamanho_janela}."
        )
        return None  # Não há dados suficientes

    ultima_janela = predicoes_limitadas[-tamanho_janela:]
    soma = sum(ultima_janela)

    if soma > limiar_compra:
        return "compra"
    elif soma < limiar_venda:
        return "venda"
    else:
        return "manter"
