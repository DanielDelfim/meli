# utils/publicidade/metricas.py
import pandas as pd

def calcular_metricas_publicidade(df_ads: pd.DataFrame, df_vendas_filtradas: pd.DataFrame) -> dict:
    """
    Calcula métricas de ACoS e TACoS a partir do DataFrame de anúncios (ads)
    e do DataFrame de vendas filtradas por codigo_do_anuncio e período.
    """
    # ACoS: investimento / receita do próprio JSON de ads
    investimento = df_ads.get("investimento_(moeda_local)", pd.Series(dtype=float)).sum()
    receita_ads = df_ads.get("receita_(moeda_local)", pd.Series(dtype=float)).sum()

    # TACoS: investimento / receita real das vendas no mesmo período e codigos
    receita_vendas = df_vendas_filtradas.get("Valor total", pd.Series(dtype=float)).sum()

    acos = (investimento / receita_ads * 100) if receita_ads > 0 else 0.0
    tacos = (investimento / receita_vendas * 100) if receita_vendas > 0 else 0.0

    return {
        "Investimento": investimento,
        "ACoS (%)": acos,
        "TACoS (%)": tacos
    }

def projetar_investimento(investimento: float, dias_base: int = 7, dias_projetados: int = 30) -> float:
    """
    Projeta o investimento para X dias, com base nos últimos Y dias.
    """
    if dias_base == 0:
        return 0.0
    return investimento / dias_base * dias_projetados

def calcular_investimento_total(df_ads: pd.DataFrame) -> float:
    """
    Retorna o total investido a partir do DataFrame de anúncios (ads),
    usando a coluna 'investimento_(moeda_local)' se disponível,
    ou 'investimento' como fallback.
    """
    if "investimento_(moeda_local)" in df_ads.columns:
        return df_ads["investimento_(moeda_local)"].sum()
    elif "investimento" in df_ads.columns:
        return df_ads["investimento"].sum()
    elif "gasto_total" in df_ads.columns:
        return df_ads["gasto_total"].sum()
    return 0.0
