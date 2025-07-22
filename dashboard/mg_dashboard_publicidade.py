import streamlit as st
import pandas as pd
from utils.utils_publicidade import preparar_dataframe_publicidade, BASE_PATH, DESIGNER_PATH
from utils.utils_dashboard import carregar_json_para_df

JSON_MG = f"{DESIGNER_PATH}/backup_vendas_mg.json"
ADS_MG = f"{BASE_PATH}/Relatorio_anuncios_patrocinados_07d_total_MG_NORMALIZADO.xlsx"


def render_mg_publicidade():
    st.header("📢 Publicidade — Minas Gerais (MG)")

    df_ads = preparar_dataframe_publicidade(JSON_MG, ADS_MG)

    if "desde" in df_ads.columns:
        df_ads["desde"] = pd.to_datetime(df_ads["desde"], errors="coerce", dayfirst=True)
    if "ate" in df_ads.columns:
        df_ads["ate"] = pd.to_datetime(df_ads["ate"], errors="coerce", dayfirst=True)

    data_inicio, data_fim = df_ads["desde"].min(), df_ads["ate"].max()

    st.sidebar.header("Filtro de Datas")
    start_date = st.sidebar.date_input("Data inicial", value=data_inicio.date() if pd.notnull(data_inicio) else None)
    end_date = st.sidebar.date_input("Data final", value=data_fim.date() if pd.notnull(data_fim) else None)

    col1, col2 = st.columns(2)
    col1.metric("Data Inicial Publicidade", data_inicio.strftime("%d/%m/%Y") if pd.notnull(data_inicio) else "N/A")
    col2.metric("Data Final Publicidade", data_fim.strftime("%d/%m/%Y") if pd.notnull(data_fim) else "N/A")

    campanhas = df_ads["campanha"].dropna().unique().tolist() if "campanha" in df_ads.columns else []
    campanha_selecionada = st.selectbox("Selecione a Campanha", ["Todas"] + campanhas)
    df_filtrado = df_ads if campanha_selecionada == "Todas" else df_ads[df_ads["campanha"] == campanha_selecionada]

    df_vendas_mg = carregar_json_para_df(JSON_MG)
    df_vendas_mg["Data da venda sem tz"] = pd.to_datetime(df_vendas_mg["Data da venda"], errors="coerce").dt.tz_localize(None)
    start_dt, end_dt = pd.to_datetime(start_date), pd.to_datetime(end_date) + pd.Timedelta(days=1)
    df_vendas_periodo = df_vendas_mg[(df_vendas_mg["Data da venda sem tz"] >= start_dt) & (df_vendas_mg["Data da venda sem tz"] <= end_dt)]

    receita_ads = df_filtrado["receita_(moeda_local)"].sum() if "receita_(moeda_local)" in df_filtrado.columns else 0
    receita_total = df_vendas_periodo["Valor total"].sum()
    receita_organica = max(receita_total - receita_ads, 0)
    investimento = df_filtrado["investimento_(moeda_local)"].sum() if "investimento_(moeda_local)" in df_filtrado.columns else 0

    acos = (investimento / receita_ads * 100) if receita_ads > 0 else 0
    tacos = (investimento / receita_total * 100) if receita_total > 0 else 0

    colunas = ["campanha", "codigo_do_anuncio", "titulo_do_anuncio_patrocinado", "impressoes", "cliques",
               "vendas_por_publicidade_(diretas_+_indiretas)", "receita_(moeda_local)", "investimento_(moeda_local)"]
    colunas = [c for c in colunas if c in df_filtrado.columns]

    st.subheader("Tabela de Publicidade")
    st.dataframe(df_filtrado[colunas], use_container_width=True)

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
    render_mg_publicidade()
