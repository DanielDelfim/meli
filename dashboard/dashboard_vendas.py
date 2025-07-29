import os
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from utils.utils_dashboard import carregar_json_para_df

# Caminhos para os JSONs pré-processados
BASE_PATH = os.getenv("BASE_PATH", r"C:/Users/dmdel/OneDrive/Aplicativos")
DESIGNER_PATH = os.path.join(BASE_PATH, "Designer")
JSON_SP_PP = os.path.join(DESIGNER_PATH, "backup_vendas_sp_pp.json")
JSON_MG_PP = os.path.join(DESIGNER_PATH, "backup_vendas_mg_pp.json")


def aplicar_filtro(df, modo, key_prefix=""):
    """Aplica filtro Diário, Mensal ou Últimos 15 dias."""
    desc = ""
    hoje = datetime.now().date()

    if modo == "Diário":
        inicio = st.sidebar.date_input("Data inicial", value=hoje, key=f"start_{key_prefix}")
        fim = st.sidebar.date_input("Data final", value=hoje, key=f"end_{key_prefix}")
        start_dt = pd.to_datetime(inicio)
        end_dt = pd.to_datetime(fim)
        mask = (df["Data da venda"] >= start_dt) & (df["Data da venda"] <= end_dt)
        desc = f"{inicio.strftime('%d/%m/%Y')} → {fim.strftime('%d/%m/%Y')}"

    elif modo == "Mensal":
        mes_ano = st.sidebar.selectbox(
            "Selecione o mês",
            options=sorted(df["Data da venda"].dt.to_period("M").unique(), reverse=True),
            format_func=lambda p: p.strftime("%B/%Y"),
            key=f"mensal_{key_prefix}"
        )
        mask = df["Data da venda"].dt.to_period("M") == mes_ano
        desc = mes_ano.strftime("%B/%Y")

    else:  # Últimos 15 dias
        end_dt = pd.to_datetime(datetime.now().date())
        start_dt = end_dt - timedelta(days=15)
        mask = (df["Data da venda"] >= start_dt) & (df["Data da venda"] <= end_dt)
        desc = f"Últimos 15 dias ({start_dt.strftime('%d/%m')} – {end_dt.strftime('%d/%m')})"

    return mask, desc


def gerar_previsao_30d(dff):
    """Gera tabela de previsão com base nos últimos 15 e 7 dias."""
    hoje = datetime.now()
    start_15d = hoje - timedelta(days=15)
    start_7d = hoje - timedelta(days=7)

    df_15 = dff[dff["Data da venda"] >= start_15d].groupby("Produto", as_index=False).agg({"Quantidade": "sum"})
    df_15.rename(columns={"Quantidade": "Qtd 15d"}, inplace=True)

    df_7 = dff[dff["Data da venda"] >= start_7d].groupby("Produto", as_index=False).agg({"Quantidade": "sum"})
    df_7.rename(columns={"Quantidade": "Qtd 7d"}, inplace=True)

    prev = pd.merge(df_15, df_7, on="Produto", how="outer").fillna(0)
    prev["Est30d_15d"] = (prev["Qtd 15d"] / 15 * 30).round().astype(int)
    prev["Est30d_7d"] = (prev["Qtd 7d"] / 7 * 30).round().astype(int)

    st.subheader("📈 Previsão de Vendas para 30 dias (baseada em 7 e 15 dias)")
    st.dataframe(prev.sort_values("Est30d_15d", ascending=False), use_container_width=True)


def render_dashboard(titulo, json_path):
    """Renderiza dashboard com filtros Diário, Mensal e Últimos 15 dias + previsão."""
    if not os.path.exists(json_path):
        st.error(f"Arquivo não encontrado: {json_path}")
        return

    st.subheader(titulo)

    try:
        df = carregar_json_para_df(json_path)
    except FileNotFoundError as e:
        st.error(str(e))
        return

    if df.empty:
        st.warning("Nenhuma venda encontrada.")
        return

    # Convertendo datas
    if "Data da venda" not in df.columns:
        st.error("Coluna 'Data da venda' não encontrada.")
        return

    df["Data da venda"] = pd.to_datetime(df["Data da venda"], errors="coerce")

    modo = st.sidebar.radio(
        f"Filtro — {titulo}",
        ["Diário", "Mensal", "Últimos 15 dias"],
        key=f"modo_{titulo}"
    )

    mask, desc = aplicar_filtro(df, modo, key_prefix=titulo)
    dff = df[mask]

    if dff.empty:
        st.warning("Sem vendas no período.")
        return

    resumo = dff.groupby("Produto", as_index=False).agg({
        "Quantidade": "sum",
        "Valor total": "sum"
    }).sort_values("Valor total", ascending=False)

    total_qt = int(dff["Quantidade"].sum())
    total_vl = dff["Valor total"].sum()

    c1, c2 = st.columns(2)
    c1.metric("Itens vendidos", total_qt)
    c2.metric("Faturamento (R$)", f"R$ {total_vl:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

    st.subheader(f"Período: {desc}")
    st.dataframe(resumo, use_container_width=True)

    if modo == "Últimos 15 dias":
        gerar_previsao_30d(dff)
