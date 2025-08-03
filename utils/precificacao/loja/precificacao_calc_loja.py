def calcular_preco_venda(produto_data):
    """
    Calcula o preço de venda com base nos dados do produto.
    Adiciona automaticamente o 'Frete de Compra (8%)'.
    :param produto_data: dicionário com as informações do produto.
    :return: preço de venda calculado (float).
    """
    preco_compra = float(produto_data.get("Preço de Compra (R$)", 0) or 0)
    frete = float(produto_data.get("Frete R$", 0) or 0)
    rotulo = float(produto_data.get("Rótulo R$", 0) or 0)
    embalagem = float(produto_data.get("Embalagem (R$)", 0) or 0)
    comissao = float(produto_data.get("% Comissão Representante", 0) or 0)
    imposto = float(produto_data.get("% Imposto Simples Nacional", 0) or 0)
    margem = float(produto_data.get("% Margem de contribuição", 0) or 0)

    # Calcula frete de compra = 8% do preço de compra
    frete_compra = preco_compra * 0.08
    produto_data["Frete de Compra (R$)"] = round(frete_compra, 2)

    # Soma dos custos diretos
    custo_total = preco_compra + frete_compra + frete + rotulo + embalagem

    # Calcula o preço de venda considerando imposto, comissão e margem
    divisor = 1 - (imposto + comissao + margem)
    if divisor <= 0:
        raise ValueError("A soma de impostos, comissão e margem não pode ser maior ou igual a 1 (100%).")

    preco_venda = custo_total / divisor
    return round(preco_venda, 2)
