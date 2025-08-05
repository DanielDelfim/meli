import pandas as pd
from utils.precificacao.precificacao_parametros import PARAMETROS_PRECIFICACAO
from utils.precificacao.meli.precificacao_io import carregar_dados, salvar_dados


def calcular_margem_contribuicao(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    for cd, parametros in PARAMETROS_PRECIFICACAO.items():
        filtro = df["CD Mercado Livre"] == cd

        imposto = parametros["% Imposto Simples Nacional"]
        marketing = parametros["% Marketing do anúncio"]

        preco_venda = df.loc[filtro, "Preço de Venda Atual (R$)"]
        preco_compra = df.loc[filtro, "Preço de Compra (R$)"]
        frete_cd = preco_compra * 0.08

        taxa_fixa = df.loc[filtro, "Taxa Fixa Mercado Livre (R$)"]
        comissao = df.loc[filtro, "% Comissão Mercado Livre"] * preco_venda
        rotulo = df.loc[filtro, "Rótulo"]
        embalagem = df.loc[filtro, "Embalagem (R$)"]
        desconto_taxas = df.loc[filtro, "Desconto em Taxas ML (R$)"]

        preco_custo_total = (
            preco_compra +
            frete_cd +
            taxa_fixa +
            comissao +
            rotulo +
            embalagem +
            (preco_venda * imposto) +
            (preco_venda * marketing) -
            desconto_taxas
        )

        margem_contribuicao = (preco_venda - preco_custo_total) / preco_venda

        df.loc[filtro, "% Margem de contribuição"] = margem_contribuicao

    return df

def calcular_e_salvar():
    df = carregar_dados()
    df_calculado = calcular_margem_contribuicao(df)
    salvar_dados(df_calculado)
    return df_calculado
