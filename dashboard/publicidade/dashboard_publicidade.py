from dashboard.publicidade.secoes_publicidade import (
    aplicar_filtros_interface,
    exibir_expander_vendas,
    exibir_expander_fora_ads,
    exibir_metricas_aggregadas,
    exibir_projecoes
)
from utils.publicidade.metricas import calcular_metricas_publicidade
from dashboard.publicidade.config_publicidade import REGION_CONFIG, DESIGNER_PATH, PUBLICIDADE_PATH
from utils.utils_filtros import filtrar_vendas_json_por_periodo
from utils.utils_publicidade import carregar_ads_json
import pandas as pd
import streamlit as st

def load_ads(path):
    df = carregar_ads_json(str(path))
    if not df.empty:
        df["desde"] = pd.to_datetime(df["desde"], errors="coerce")
        df["ate"] = pd.to_datetime(df["ate"], errors="coerce")
        df["codigo_do_anuncio"] = df["codigo_do_anuncio"].astype(str).str.strip()
    return df

def render_publicidade(region_key: str):
    cfg = REGION_CONFIG[region_key]
    df_ads7 = load_ads(PUBLICIDADE_PATH / cfg["ads_7d"])
    df_ads15 = load_ads(PUBLICIDADE_PATH / cfg["ads_15d"])
    df_ads30 = load_ads(PUBLICIDADE_PATH / cfg["ads_30d"])
    df_ads_geral = pd.concat([df_ads7, df_ads15, df_ads30])

    min_date = df_ads_geral["desde"].min().date()
    max_date = df_ads_geral["ate"].max().date()

    df_vendas_geral = filtrar_vendas_json_por_periodo(
        caminho_json=str(DESIGNER_PATH / cfg["vendas"]),
        data_inicio=min_date,
        data_fim=max_date,
        unidade=region_key
    )
    df_vendas_geral["codigo_do_anuncio"] = df_vendas_geral.get("codigo_do_anuncio", "").astype(str)

    st.header(f"📢 Publicidade — {cfg['display_name']}")
    campanha, titulo = aplicar_filtros_interface(df_ads_geral)

    def filtrar(df):  # função inline para reaproveitar
        df = df.copy()
        if campanha != "Todas":
            df = df[df["campanha"] == campanha]
        if titulo != "Todos":
            df = df[df["titulo_do_anuncio_patrocinado"] == titulo]
        return df

    ads7 = filtrar(df_ads7)
    ads15 = filtrar(df_ads15)
    ads30 = filtrar(df_ads30)

    # Filtro por período com base nas datas reais dos anúncios
    vendas7 = filtrar_vendas_json_por_periodo(
    caminho_json=str(DESIGNER_PATH / cfg["vendas"]),
    data_inicio=ads7["desde"].min().date(),
    data_fim=ads7["ate"].max().date(),
    unidade=region_key
)
    vendas7 = vendas7[vendas7["codigo_do_anuncio"].isin(ads7["codigo_do_anuncio"])]

    vendas15 = filtrar_vendas_json_por_periodo(
    caminho_json=str(DESIGNER_PATH / cfg["vendas"]),
    data_inicio=ads15["desde"].min().date(),
    data_fim=ads15["ate"].max().date(),
    unidade=region_key
)
    vendas15 = vendas15[vendas15["codigo_do_anuncio"].isin(ads15["codigo_do_anuncio"])]

    vendas30 = filtrar_vendas_json_por_periodo(
    caminho_json=str(DESIGNER_PATH / cfg["vendas"]),
    data_inicio=ads30["desde"].min().date(),
    data_fim=ads30["ate"].max().date(),
    unidade=region_key
)
    vendas30 = vendas30[vendas30["codigo_do_anuncio"].isin(ads30["codigo_do_anuncio"])]


    exibir_expander_vendas(vendas30)
    exibir_expander_fora_ads(df_vendas_geral, df_ads_geral)

    m7 = calcular_metricas_publicidade(ads7, vendas7)
    m15 = calcular_metricas_publicidade(ads15, vendas15)
    m30 = calcular_metricas_publicidade(ads30, vendas30)


    exibir_metricas_aggregadas(m7, m15, m30)
    exibir_projecoes(m7, m15)
