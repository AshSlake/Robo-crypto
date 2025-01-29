def filtrar_palavras_irrelevantes():
    # Remove palavras irrelevantes
    palavras_a_ignorar = [
        # Palavras originais
        "sobrevendido",
        "sobrevenda",
        "sobrecomprado",
        "vendida",
        "vendido",
        "comprado",
        "sobrecompra",
        "força de compra",
        "força de venda",
        "níveis de venda",
        "zona de compra",
        "zona de venda",
        "níveis de compra",
        # Palavras adicionais
        # Relacionadas a venda e compra
        "pressão de venda",
        "pressão de compra",
        "força compradora",
        "força vendedora",
        "demanda de venda",
        "demanda de compra",
        "volume de venda",
        "volume de compra",
        "oportunidade clara de compra",
        "compra ou venda",
        "antes de tomar uma decisão de compra",
        "antes de assumir uma posição comprada",
        "antes de considerar uma compra",
        "antes de assumir uma posição vendida",
        "antes de tomar uma decisão de venda",
        "antes de assumir uma posição vendida",
        # Relacionadas a compra e venda
        "compra forte",
        # Termos técnicos comuns
        "tendência de venda",
        "tendência de compra",
        "potencial de venda",
        "potencial de compra",
        "indicador de venda",
        "indicador de compra",
        # Descrições confusas
        "condições de venda",
        "condições de compra",
        "em zona de venda",
        "em zona de compra",
        "oportunidade de venda",
        "oportunidade de compra",
        # Outros termos que podem causar ruído
        "momentum de venda",
        "momentum de compra",
        "overbought",  # Caso use termos em inglês
        "oversold",  # Caso use termos em inglês
        "limiar de compra",
        "limiar de venda",
    ]
    return palavras_a_ignorar
