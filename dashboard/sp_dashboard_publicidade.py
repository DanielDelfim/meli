import streamlit as st
import pandas as pd
import calendar
import json
from datetime import datetime
from pathlib import Path
from utils.utils_dashboard import carregar_json_para_df
from utils.utils_publicidade import carregar_ads_json, DESIGNER_PATH

# Paths dos JSONs de publicidade e precificação
JSON_SP      = f"{DESIGNER_PATH}/backup_vendas_sp.json"
ADS_WEEK_SP  = f"{DESIGNER_PATH}/ads_sp.json"        # Últimos 7 dias
ADS_MONTH_SP = f"{DESIGNER_PATH}/ads_mes_sp.json"    # Mês até hoje
HIST_PATH    = f"{DESIGNER_PATH}/historico_sp.json"  # Histórico de SP
PREC_PATH    = str(Path(DESIGNER_PATH).parent / "tokens" / "precificacao_meli.json")


def render_sp_publicidade():
    st.header("📢 Publicidade — São Paulo (SP)")

    # --- Carregar dados de publicidade ---
    df_week = carregar_ads_json(ADS_WEEK_SP)
    if df_week.empty:
        st.warning("Nenhum dado de publicidade encontrado.")
        return
    # Converter datas
    df_week["desde"] = pd.to_datetime(df_week["desde"], format="%d-%b-%Y", dayfirst=True, errors="coerce")
    df_week["ate"]   = pd.to_datetime(df_week["ate"],   format="%d-%b-%Y", dayfirst=True, errors="coerce")

    # --- Sidebar: filtros ---
    data_inicio = df_week["desde"].min().date()
    data_fim    = df_week["ate"].max().date()
    st.sidebar.header("Filtros — SP")
    start_date = st.sidebar.date_input("Data inicial", value=data_inicio)
    end_date   = st.sidebar.date_input("Data final",   value=data_fim)
    start_dt = pd.to_datetime(start_date)
    end_dt   = pd.to_datetime(end_date) + pd.Timedelta(days=1)

    df_filtrado = df_week[(df_week["desde"] < end_dt) & (df_week["ate"] >= start_dt)].copy()
    has_ads = not df_filtrado.empty
    st.subheader(f"Período: {start_date.strftime('%d/%m/%Y')} → {end_date.strftime('%d/%m/%Y')}")

    # --- Carregar dados de vendas ---
    df_vendas = carregar_json_para_df(JSON_SP)
    df_vendas["Data da venda"] = pd.to_datetime(df_vendas["Data da venda"], errors="coerce")
    mask_v = (df_vendas["Data da venda"] >= start_dt) & (df_vendas["Data da venda"] < end_dt)
    if has_ads and "codigo_do_anuncio" in df_filtrado and "codigo_do_anuncio" in df_vendas:
        mask_v &= df_vendas["codigo_do_anuncio"].isin(df_filtrado["codigo_do_anuncio"].unique())
    df_vendas_periodo = df_vendas[mask_v]

    # --- Métricas SP ---
    receita_ads    = df_filtrado["receita_(moeda_local)"].sum() if has_ads else 0.0
    investimento_w = df_filtrado["investimento_(moeda_local)"].sum() if has_ads else 0.0
    receita_total  = df_vendas_periodo["Valor total"].sum()
    receita_org    = max(receita_total - receita_ads, 0)
    acos           = investimento_w / receita_ads * 100 if receita_ads > 0 else 0
    tacos          = investimento_w / receita_total * 100 if receita_total > 0 else 0

    # --- Tabela de Publicidade ---
    if has_ads:
        st.subheader("Publicidade Detalhada")
        df_show = df_filtrado.rename(columns={
            "titulo_do_anuncio_patrocinado": "Título",
            "impressoes": "Impressões",
            "cliques": "Cliques",
            "investimento_(moeda_local)": "Investimento (R$)"
        })[["Título","Impressões","Cliques","Investimento (R$)"]]
        st.dataframe(df_show, use_container_width=True, hide_index=True)

    # --- Métricas Gerais (7 dias) ---
    st.markdown("### Métricas Gerais (7 dias)")
    col1, col2, col3, col4 = st.columns(4)
    ctr = df_filtrado['cliques'].sum() / df_filtrado['impressoes'].sum() * 100 if has_ads else 0
    cvr = df_filtrado['vendas_por_publicidade_(diretas_+_indiretas)'].sum() / df_filtrado['cliques'].sum() * 100 if has_ads else 0
    col1.metric("CTR", f"{ctr:.2f}%")
    col2.metric("CVR", f"{cvr:.2f}%")
    col3.metric("ACOS", f"{acos:.2f}%")
    col4.metric("TACOS", f"{tacos:.2f}%")

    # --- Receitas e Investimento (7 dias) ---
    st.markdown("### Receitas e Investimento (7 dias)")
    r1, r2, r3 = st.columns(3)
    r1.metric("Receita Ads", f"R$ {receita_ads:,.2f}")
    r2.metric("Receita Orgânica", f"R$ {receita_org:,.2f}")
    r3.metric("Investimento (7d)", f"R$ {investimento_w:,.2f}")

    # --- Previsões ---
    inv_month    = carregar_ads_json(ADS_MONTH_SP)["investimento_(moeda_local)"].sum()
    dias_obs     = (df_week['ate'].max() - df_week['desde'].min()).days + 1
    media_diaria = df_week['investimento_(moeda_local)'].sum() / dias_obs if dias_obs > 0 else 0
    dias_rest    = calendar.monthrange(datetime.now().year, datetime.now().month)[1] - datetime.now().day
    prev_rest    = media_diaria * dias_rest
    proj_mes     = inv_month + prev_rest
    proj_30      = media_diaria * 30
    st.markdown("---")
    st.subheader("Previsões")
    df_pre = pd.DataFrame({
        'Métrica': [
            f"Investimento Até Agora ({datetime.now().strftime('%m/%Y')})",
            f"Previsão Restante",
            f"Projeção Total",
            'Previsão 30 Dias'
        ],
        'Valor': [inv_month, prev_rest, proj_mes, proj_30]
    })
    df_pre['Valor'] = df_pre['Valor'].apply(lambda x: f"R$ {x:,.2f}")
    st.dataframe(df_pre, use_container_width=True, hide_index=True)

    # --- Cards Receita Geral Período e TACOS Geral ---
    st.markdown("---")
    today = datetime.now()
    first = datetime(today.year, today.month, 1)
    vendas_mes = df_vendas[(df_vendas['Data da venda'] >= first) & (df_vendas['Data da venda'] <= today)]['Valor total'].sum()
    tacos_h_global = inv_month / vendas_mes * 100 if vendas_mes > 0 else 0
    c1, c2 = st.columns(2)
    c1.metric("Receita Geral dia 1 até hoje", f"R$ {vendas_mes:,.2f}")
    c2.metric("TACOS Geral", f"{tacos_h_global:.2f}%")

if __name__ == "__main__":
    render_sp_publicidade()
