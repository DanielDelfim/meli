import os
import streamlit as st
import pandas as pd
import calendar
from datetime import datetime, date
from pathlib import Path
from utils.utils_dashboard import carregar_json_para_df
from utils.utils_publicidade import carregar_ads_json, DESIGNER_PATH

# ---------------- CONFIGURAÇÕES DE REGIÃO ----------------
REGION_CONFIG = {
    "SP": {
        "display_name": "São Paulo (SP)",
        "vendas": "backup_vendas_sp_pp.json",
        "ads_week": "ads_sp.json",
        "ads_month": "ads_mes_sp.json",
    },
    "MG": {
        "display_name": "Minas Gerais (MG)",
        "vendas": "backup_vendas_mg_pp.json",
        "ads_week": "ads_mg.json",
        "ads_month": "ads_mes_mg.json",
    },
}

# ---------------- PREPARAR VENDAS ----------------
def preparar_vendas_pp(path_vendas: str) -> pd.DataFrame:
    """Lê o backup_vendas_*_pp.json e retorna um DataFrame com vendas simples"""
    df = carregar_json_para_df(path_vendas)
    if df.empty:
        return pd.DataFrame(columns=["Data da venda","Produto","Quantidade","Valor total","SKU"])
    df = df.copy()
    # padroniza data para date
    df["Data da venda"] = pd.to_datetime(df["Data da venda"], errors="coerce").dt.date
    # garante coluna SKU existente (pode vir de SKU ou codigo_do_anuncio)
    if "SKU" not in df.columns:
        df["SKU"] = df.get("codigo_do_anuncio", None)
    return df

# ---------------- DASHBOARD ----------------
def render_publicidade(region_key: str):
    cfg = REGION_CONFIG[region_key]
    display_name = cfg["display_name"]
    st.header(f"📢 Publicidade — {display_name}")

    base = Path(DESIGNER_PATH)
    vendas_path    = base / cfg["vendas"]
    ads_week_path  = base / cfg["ads_week"]
    ads_month_path = base / cfg["ads_month"]

    # --- Dados semanais de publicidade ---
    df_week = carregar_ads_json(str(ads_week_path))
    if df_week.empty:
        st.warning("Nenhum dado de publicidade encontrado.")
        return
    # converte datas para date
    for col in ["desde", "ate"]:
        if col in df_week.columns:
            df_week[col] = pd.to_datetime(df_week[col], format="%d-%b-%Y", dayfirst=True, errors="coerce").dt.date

    # --- Filtros de data ---
    st.sidebar.header(f"Filtros — {display_name}")
    data_inicio = df_week["desde"].min()
    data_fim    = df_week["ate"].max()
    start_date  = st.sidebar.date_input("Data inicial", value=data_inicio, key=f"inicio_{region_key}")
    end_date    = st.sidebar.date_input("Data final",   value=data_fim,   key=f"fim_{region_key}")
    
    # mascaras
    mask_ads = (df_week["desde"] <= end_date) & (df_week["ate"] >= start_date)
    df_ads_periodo = df_week.loc[mask_ads].copy()
    has_ads = not df_ads_periodo.empty
    st.subheader(f"Período: {start_date.strftime('%d/%m/%Y')} → {end_date.strftime('%d/%m/%Y')}")

    # --- Vendas no período ---
    df_vendas = preparar_vendas_pp(str(vendas_path))
    mask_v  = (df_vendas["Data da venda"] >= start_date) & (df_vendas["Data da venda"] <= end_date)
    df_vendas_periodo = df_vendas.loc[mask_v].copy()

    # --- Filtro opcional por SKU (só se SKU selecionado diferente de Todos) ---
    skus = sorted(df_vendas_periodo["SKU"].dropna().unique())
    sku_sel = st.sidebar.selectbox("Filtrar por SKU", ["Todos"] + skus, key=f"sku_{region_key}")
    if sku_sel and sku_sel != "Todos":
        df_vendas_periodo = df_vendas_periodo[df_vendas_periodo["SKU"] == sku_sel].copy()

    # --- Cálculo de métricas ---
    receita_total = df_vendas_periodo["Valor total"].sum()
    receita_ads   = df_ads_periodo.get("receita_(moeda_local)", pd.Series(dtype=float)).sum() if has_ads else 0.0
    receita_org   = receita_total - receita_ads
    investimento  = df_ads_periodo.get("investimento_(moeda_local)", pd.Series(dtype=float)).sum() if has_ads else 0.0
    acos          = (investimento / receita_ads * 100) if receita_ads > 0 else 0.0
    tacos         = (investimento / receita_total * 100) if receita_total > 0 else 0.0

    # --- Publicidade Detalhada ---
    if has_ads:
        st.subheader("Publicidade Detalhada")
        df_show = df_ads_periodo.rename(columns={
            "titulo_do_anuncio_patrocinado": "Título",
            "impressoes": "Impressões",
            "cliques": "Cliques",
            "investimento_(moeda_local)": "Investimento (R$)",
            "receita_(moeda_local)": "Receita Ads"
        })[["Título", "Impressões", "Cliques", "Investimento (R$)", "Receita Ads"]]
        st.dataframe(df_show, use_container_width=True, hide_index=True)

    # --- Métricas Gerais (7 dias) ---
    st.markdown("### Métricas Gerais (7 dias)")
    c1, c2, c3, c4 = st.columns(4)
    ctr = (df_ads_periodo['cliques'].sum() / df_ads_periodo['impressoes'].sum() * 100) if has_ads else 0.0
    cvr = (df_ads_periodo['vendas_por_publicidade_(diretas_+_indiretas)'].sum() / df_ads_periodo['cliques'].sum() * 100) if has_ads else 0.0
    c1.metric("CTR", f"{ctr:.2f}%")
    c2.metric("CVR", f"{cvr:.2f}%")
    c3.metric("ACOS", f"{acos:.2f}%")
    c4.metric("TACOS", f"{tacos:.2f}%")

    # --- Receitas e Investimento (7 dias) ---
    st.markdown("### Receitas e Investimento (7 dias)")
    r1, r2, r3 = st.columns(3)
    r1.metric("Receita Ads", f"R$ {receita_ads:,.2f}")
    r2.metric("Receita Orgânica", f"R$ {receita_org:,.2f}")
    r3.metric("Investimento (7d)", f"R$ {investimento:,.2f}")

    # --- Previsões ---
    df_month_ads = carregar_ads_json(str(ads_month_path))
    if not df_month_ads.empty:
        for col in ["desde", "ate"]:
            if col in df_month_ads.columns:
                df_month_ads[col] = pd.to_datetime(df_month_ads[col], format="%d-%b-%Y", dayfirst=True, errors="coerce").dt.date
    inv_month = df_month_ads.get("investimento_(moeda_local)", pd.Series(dtype=float)).sum()
    dias_obs  = ((df_month_ads['ate'].max() - df_month_ads['desde'].min()).days + 1) if not df_month_ads.empty else 0
    media_d   = df_month_ads['investimento_(moeda_local)'].sum() / dias_obs if dias_obs > 0 else 0.0
    dias_rest = calendar.monthrange(datetime.now().year, datetime.now().month)[1] - datetime.now().day
    prev_rest = media_d * dias_rest
    proj_mes  = inv_month + prev_rest
    proj_30   = media_d * 30
    st.markdown("---")
    st.subheader("Previsões")
    df_pre = pd.DataFrame({
        'Métrica': [
            f"Investimento Até Agora ({datetime.now().strftime('%m/%Y')})",
            "Previsão Restante",
            "Projeção Total",
            "Previsão 30 Dias"
        ],
        'Valor': [inv_month, prev_rest, proj_mes, proj_30]
    })
    df_pre['Valor'] = df_pre['Valor'].apply(lambda x: f"R$ {x:,.2f}")
    st.dataframe(df_pre, use_container_width=True, hide_index=True)

    # --- Cards Mensais ---
    hoje = date.today()
    if not df_month_ads.empty:
        primeiro = df_month_ads['desde'].min()
        ultimo   = df_month_ads['ate'].max()
    else:
        primeiro = hoje.replace(day=1)
        ultimo   = hoje
    vendas_mes = df_vendas.loc[(df_vendas['Data da venda'] >= primeiro) & (df_vendas['Data da venda'] <= ultimo), 'Valor total'].sum()
    tacos_g = (inv_month / vendas_mes * 100) if vendas_mes > 0 else 0.0
    st.markdown("---")
    c1, c2 = st.columns(2)
    c1.metric("Receita Geral dia 1 até final do mês", f"R$ {vendas_mes:,.2f}")
    c2.metric("TACOS Geral", f"{tacos_g:.2f}%")

if __name__ == "__main__":
    st.sidebar.title("Configurações")
    region = st.sidebar.radio("Selecione a região", list(REGION_CONFIG.keys()), index=0)
    render_publicidade(region)
