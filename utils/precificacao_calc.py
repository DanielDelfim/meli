def calcular_margens(dados):
    """
    Calcula frete até CD, imposto, custo total, lucro real e margem de contribuição (%).
    Pode receber um dicionário ou um objeto com atributos.

    Retorna:
        (frete_cd, imposto, custo_total, lucro_real, margem_real_pct)
    """

    # Extrair valores, considerando se é dict ou objeto
    def get_val(chave):
        if isinstance(dados, dict):
            return float(dados.get(chave, 0) or 0)
        return float(getattr(dados, chave, 0) or 0)

    preco_venda = get_val("Preço de Venda Atual (R$)")
    preco_compra = get_val("Preço de Compra (R$)")
    rotulo = get_val("Rótulo")
    embalagem = get_val("Embalagem (R$)")
    comissao_ml = get_val("% Comissão Mercado Livre")
    marketing = get_val("% Marketing do anúncio")
    frete_ml = get_val("Frete Mercado Livre (R$)")
    taxa_fixa_ml = get_val("Taxa Fixa Mercado Livre (R$)")
    desconto_taxas_ml = get_val("Desconto em Taxas ML (R$)")

    # --- Cálculos principais ---
    frete_cd = preco_compra * 0.08  # 8% do preço de compra
    imposto = preco_venda * 0.10    # 10% do preço de venda

    # Custo total
    custo_total = (
        preco_compra +
        frete_cd +
        rotulo +
        embalagem +
        frete_ml +
        taxa_fixa_ml -
        desconto_taxas_ml +
        (preco_venda * comissao_ml) +
        (preco_venda * marketing) +
        imposto
    )

    # Lucro real
    lucro_real = preco_venda - custo_total

    # Margem de contribuição em porcentagem
    margem_real_pct = (lucro_real / preco_venda * 100) if preco_venda else 0

    return round(frete_cd, 2), round(imposto, 2), round(custo_total, 2), round(lucro_real, 2), round(margem_real_pct, 2)
