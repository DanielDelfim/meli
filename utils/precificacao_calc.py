def calcular_margens(dados, json_base=None):
    """
    Calcula frete até CD, imposto, custo total, lucro real e margem de contribuição (%).
    Caso o dicionário 'dados' não contenha todos os campos, busca os valores faltantes no json_base.

    Retorna:
        (frete_cd, imposto, custo_total, lucro_real, margem_real_pct)
    """
    def get_val(chave):
        # Primeiro busca no dicionário de edição
        val = dados.get(chave) if isinstance(dados, dict) else getattr(dados, chave, None)
        if val is not None and val != "":
            return float(val)
        # Se não existir, tenta buscar no json_base
        if json_base and chave in json_base:
            return float(json_base.get(chave) or 0)
        return 0.0

    preco_venda = get_val("Preço de Venda Atual (R$)")
    preco_compra = get_val("Preço de Compra (R$)")
    rotulo = get_val("Rótulo")
    embalagem = get_val("Embalagem (R$)")
    comissao_ml = get_val("% Comissão Mercado Livre")
    marketing = get_val("% Marketing do anúncio")
    frete_ml = get_val("Frete Mercado Livre (R$)")
    taxa_fixa_ml = get_val("Taxa Fixa Mercado Livre (R$)")
    desconto_taxas_ml = get_val("Desconto em Taxas ML (R$)")
    imposto_sn = get_val("% Imposto Simples Nacional")

    # --- Cálculos principais ---
    frete_cd = get_val("Frete até cd (R$)") or preco_compra * 0.08
    imposto = preco_venda * imposto_sn if imposto_sn else preco_venda * 0.10

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

    lucro_real = preco_venda - custo_total
    margem_real_pct = (lucro_real / preco_venda * 100) if preco_venda else 0

    return round(frete_cd, 2), round(imposto, 2), round(custo_total, 2), round(lucro_real, 2), round(margem_real_pct, 2)
