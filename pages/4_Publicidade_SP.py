import streamlit as st
import pandas as pd
from utils.utils_dashboard import carregar_json_para_df
from utils.utils_publicidade import carregar_ads_json, DESIGNER_PATH

JSON_SP = f"{DESIGNER_PATH}/backup_vendas_sp.json"
ADS_SP = f"{DESIGNER_PATH}/ads_sp.json"


def render_sp_publicidade():
    st.header("📢 Publicidade — São Paulo (SP)")

    # --- Carregar dados de publicidade ---
    df_ads = carregar_ads_json(ADS_SP)
    if df_ads.empty:
        st.warning("Nenhum dado de publicidade encontrado.")
        return

    # Ajustar datas
    if "desde" in df_ads.columns:
        df_ads["desde"] = pd.to_datetime(df_ads["desde"], errors="coerce", dayfirst=True)
    if "ate" in df_ads.columns:
        df_ads["ate"] = pd.to_datetime(df_ads["ate"], errors="coerce", dayfirst=True)

    # Período padrão (min e max do JSON)
    data_inicio_default = df_ads["desde"].min().date()
    data_fim_default = df_ads["ate"].max().date()

    # --- Filtro Diário ---
    st.sidebar.header("Filtro Diário — Publicidade SP")
    start_date = st.sidebar.date_input("Data inicial", value=data_inicio_default)
    end_date   = st.sidebar.date_input("Data final",   value=data_fim_default)

    start_dt = pd.to_datetime(start_date)
    end_dt   = pd.to_datetime(end_date) + pd.Timedelta(days=1)  # intervalo [start, end)

    # Interseção de períodos de ADS
    mask_date = (df_ads["desde"] < end_dt) & (df_ads["ate"] >= start_dt)
    df_filtrado = df_ads[mask_date].copy()

    # --- Filtro por campanha ---
    if "campanha" in df_filtrado.columns:
        campanhas = sorted(df_filtrado["campanha"].dropna().unique().tolist())
        campanha_selecionada = st.sidebar.selectbox("Filtrar por Campanha:", ["Todas"] + campanhas)
        if campanha_selecionada != "Todas":
            df_filtrado = df_filtrado[df_filtrado["campanha"] == campanha_selecionada]

    # --- Filtro por anúncio ---
    if "titulo_do_anuncio_patrocinado" in df_filtrado.columns:
        anuncios = sorted(df_filtrado["titulo_do_anuncio_patrocinado"].dropna().unique().tolist())
        anuncio_selecionado = st.sidebar.selectbox("Filtrar por Anúncio:", ["Todos"] + anuncios)
        if anuncio_selecionado != "Todos":
            df_filtrado = df_filtrado[df_filtrado["titulo_do_anuncio_patrocinado"] == anuncio_selecionado]

    st.subheader(f"Período ➔ {start_dt.strftime('%d/%m/%Y')} → {(end_dt - pd.Timedelta(seconds=1)).strftime('%d/%m/%Y')}")

    # --- Carregar dados de vendas ---
    df_vendas_sp = carregar_json_para_df(JSON_SP)
    df_vendas_sp["Data da venda"] = pd.to_datetime(df_vendas_sp["Data da venda"], errors="coerce")

    # Filtro por data em vendas
    mask_vendas_date = (df_vendas_sp["Data da venda"] >= start_dt) & (df_vendas_sp["Data da venda"] < end_dt)

    # Filtro por código (se existir nas duas bases)
    cod_col = "codigo_do_anuncio"
    if cod_col in df_vendas_sp.columns and cod_col in df_filtrado.columns:
        codigos = df_filtrado[cod_col].dropna().unique()
        mask_vendas_code = df_vendas_sp[cod_col].isin(codigos) if len(codigos) else True
    else:
        mask_vendas_code = True

    df_vendas_periodo = df_vendas_sp[mask_vendas_date & mask_vendas_code]

    # --- Métricas ---
    receita_ads     = df_filtrado.get("receita_(moeda_local)", pd.Series([0])).sum()
    investimento    = df_filtrado.get("investimento_(moeda_local)", pd.Series([0])).sum()
    receita_total   = df_vendas_periodo["Valor total"].sum()
    receita_organica = max(receita_total - receita_ads, 0)

    acos  = (investimento / receita_ads  * 100) if receita_ads  > 0 else 0
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

    # --- Cards ---
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
