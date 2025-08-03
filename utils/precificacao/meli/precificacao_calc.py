import math

def calcular_margens(dados, json_base=None):
    def get_val(chave):
        if isinstance(dados, dict):
            val = dados.get(chave)
        else:
            val = getattr(dados, chave, None)

        if val is None or val == "" or (isinstance(val, float) and math.isnan(val)):
            if json_base and chave in json_base:
                jb = json_base.get(chave)
                if jb is None or (isinstance(jb, float) and math.isnan(jb)):
                    return 0.0
                return float(jb)
            return 0.0
        return float(val)

    preco_venda    = get_val("Preço de Venda Atual (R$)")
    preco_compra   = get_val("Preço de Compra (R$)")
    rotulo         = get_val("Rótulo")
    embalagem      = get_val("Embalagem (R$)")
    comissao_ml    = get_val("% Comissão Mercado Livre")
    marketing      = get_val("% Marketing do anúncio")
    frete_ml       = get_val("Frete Mercado Livre (R$)")
    taxa_fixa_ml   = get_val("Taxa Fixa Mercado Livre (R$)")
    desconto_ml    = get_val("Desconto em Taxas ML (R$)")
    imposto_sn     = get_val("% Imposto Simples Nacional")

    # Frete CD sempre como 8% do preço de compra
    frete_cd = round(preco_compra * 0.08, 2)

    imposto = round(preco_venda * (imposto_sn or 0.10), 2)

    custo_total = (
        preco_compra + frete_cd + rotulo + embalagem + frete_ml + taxa_fixa_ml
        - desconto_ml + preco_venda * comissao_ml + preco_venda * marketing + imposto
    )

    lucro_real = preco_venda - custo_total
    margem_real_pct = (lucro_real / preco_venda * 100) if preco_venda else 0.0

    return (
        frete_cd,
        imposto,
        round(custo_total, 2),
        round(lucro_real, 2),
        round(margem_real_pct, 2)
    )
