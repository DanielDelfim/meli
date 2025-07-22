import streamlit as st
import pandas as pd
from utils.utils_publicidade import carregar_ads_json
from utils.utils_dashboard import carregar_json_para_df, DESIGNER_PATH

JSON_SP = f"{DESIGNER_PATH}/backup_vendas_sp.json"
ADS_SP = f"{DESIGNER_PATH}/ads_sp.json"

def render_sp_publicidade():
    st.header("📢 Publicidade — São Paulo (SP)")

    # --- Carregar dados de publicidade ---
    try:
        df_ads = carregar_ads_json(ADS_SP)
    except FileNotFoundError:
        st.error("Arquivo de publicidade SP não encontrado!")
        return

    # Garantir datas em datetime
    if "desde" in df_ads.columns:
        df_ads["desde"] = pd.to_datetime(df_ads["desde"], errors="coerce", dayfirst=True)
    if "ate" in df_ads.columns:
        df_ads["ate"] = pd.to_datetime(df_ads["ate"], errors="coerce", dayfirst=True)

    data_inicio = df_ads["desde"].min() if "desde" in df_ads.columns else None
    data_fim = df_ads["ate"].max() if "ate" in df_ads.columns else None

    # --- Filtro lateral de datas ---
    st.sidebar.header("Filtro de Datas")
    start_date = st.sidebar.date_input("Data inicial", value=data_inicio.date() if pd.notnull(data_inicio) else None)
    end_date = st.sidebar.date_input("Data final", value=data_fim.date() if pd.notnull(data_fim) else None)

    # --- Filtro por campanha ---
    campanhas = df_ads["campanha"].dropna().unique().tolist() if "campanha" in df_ads.columns else []
    campanha_selecionada = st.selectbox("Selecione a Campanha", ["Todas"] + campanhas)
    df_filtrado = df_ads if campanha_selecionada == "Todas" else df_ads[df_ads["campanha"] == campanha_selecionada]

    # --- Carregar JSON de vendas ---
    try:
        df_vendas_sp = carregar_json_para_df(JSON_SP)
    except FileNotFoundError:
        st.error("Arquivo de vendas SP não encontrado!")
        return

    # Remover timezone para evitar erros de comparação
    df_vendas_sp["Data da venda sem tz"] = pd.to_datetime(df_vendas_sp["Data da venda"], errors="coerce").dt.tz_localize(None)
    start_dt, end_dt = pd.to_datetime(start_date), pd.to_datetime(end_date) + pd.Timedelta(days=1)
    df_vendas_periodo = df_vendas_sp[(df_vendas_sp["Data da venda sem tz"] >= start_dt) & (df_vendas_sp["Data da venda sem tz"] <= end_dt)]

    # --- Receita total filtrada pelos anúncios ---
    anuncios_ads = df_filtrado["codigo_do_anuncio"].dropna().unique().tolist()
    vendas_relacionadas = df_vendas_periodo[df_vendas_periodo["codigo_do_anuncio"].isin(anuncios_ads)]

    receita_total = vendas_relacionadas["Valor total"].sum()
    receita_ads = df_filtrado["receita_(moeda_local)"].sum() if "receita_(moeda_local)" in df_filtrado.columns else 0
    receita_organica = max(receita_total - receita_ads, 0)
    investimento = df_filtrado["investimento_(moeda_local)"].sum() if "investimento_(moeda_local)" in df_filtrado.columns else 0

    acos = (investimento / receita_ads * 100) if receita_ads > 0 else 0
    tacos = (investimento / receita_total * 100) if receita_total > 0 else 0

    # --- Tabela ---
    colunas = [
        "campanha", "codigo_do_anuncio", "titulo_do_anuncio_patrocinado",
        "impressoes", "cliques", "vendas_por_publicidade_(diretas_+_indiretas)",
        "receita_(moeda_local)", "investimento_(moeda_local)"
    ]
    colunas = [c for c in colunas if c in df_filtrado.columns]

    st.subheader("Tabela de Publicidade")
    st.dataframe(df_filtrado[colunas], use_container_width=True)

    # --- Métricas gerais ---
    impressoes = df_filtrado["impressoes"].sum() if "impressoes" in df_filtrado.columns else 0
    cliques = df_filtrado["cliques"].sum() if "cliques" in df_filtrado.columns else 0
    vendas_ads = df_filtrado["vendas_por_publicidade_(diretas_+_indiretas)"].sum() if "vendas_por_publicidade_(diretas_+_indiretas)" in df_filtrado.columns else 0
    ctr = (cliques / impressoes * 100) if impressoes > 0 else 0
    cvr = (vendas_ads / cliques * 100) if cliques > 0 else 0

    st.markdown("### Métricas Gerais")
    col1, col2, col3 = st.columns(3)
    col1.metric("CTR (Taxa de Cliques)", f"{ctr:.2f}%")
    col2.metric("CVR (Taxa de Conversão)", f"{cvr:.2f}%")
    col3.metric("ACOS / TACOS", f"{acos:.2f}% / {tacos:.2f}%")

    st.markdown("### Receitas e Investimento")
    col4, col5, col6 = st.columns(3)
    col4.metric("Receita por Ads (R$)", f"R$ {receita_ads:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    col5.metric("Receita Orgânica (R$)", f"R$ {receita_organica:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    col6.metric("Investimento (R$)", f"R$ {investimento:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))


if __name__ == "__main__":
    render_sp_publicidade()
