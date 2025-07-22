import streamlit as st
import pandas as pd
import plotly.express as px
from utils.utils_dashboard import carregar_json_para_df, preparar_periodos, aplicar_filtro

def render_mg():
    st.header("📍 Dashboard de Vendas — Minas Gerais")

    try:
        df = carregar_json_para_df("C:/Users/dmdel/OneDrive/Aplicativos/Designer/backup_vendas_mg.json")
    except FileNotFoundError as e:
        st.error(str(e))
        return

    if df.empty:
        st.warning("Nenhuma venda encontrada no JSON.")
        return

    # --- Prepara períodos ---
    labels, label_map = preparar_periodos(df)

    # --- Filtro de período ---
    modo = st.sidebar.radio("Filtrar por:", ["Diário", "Mensal", "Últimos 15 dias"])
    mask, filtro_descr = aplicar_filtro(df, modo)

    if modo == "Diário":
        st.sidebar.header("Filtro Diário")
        start_date = st.sidebar.date_input("Data inicial", value=df["Data da venda"].min().date())
        end_date = st.sidebar.date_input("Data final", value=df["Data da venda"].max().date())
        start_dt = pd.to_datetime(start_date)
        end_dt = pd.to_datetime(end_date) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
        mask = (df["Data da venda"] >= start_dt) & (df["Data da venda"] <= end_dt)
        filtro_descr = f"{start_dt.strftime('%d/%m/%y')} → {end_dt.strftime('%d/%m/%y')}"

    if modo == "Mensal":
        st.sidebar.header("Filtro Mensal")
        selecionados = st.sidebar.multiselect("Mês/Ano", options=labels, default=labels)
        sel_periods = [p for p, lbl in label_map.items() if lbl in selecionados]
        mask = df["period"].isin(sel_periods)
        filtro_descr = ", ".join(selecionados)

    dff = df[mask]
    if dff.empty:
        st.warning("Nenhuma venda encontrada para o período selecionado.")
        return

    # --- Resumo de vendas ---
    df_resumo = (
        dff.groupby("Produto", as_index=False)
        .agg({"Quantidade": "sum", "Valor total": "sum"})
        .sort_values("Valor total", ascending=False)
    )

    # --- Métricas principais ---
    total_qt = int(dff["Quantidade"].sum())
    total_vl = dff["Valor total"].sum()
    col1, col2 = st.columns(2)
    col1.metric("Itens vendidos", total_qt)
    col2.metric(
        "Faturamento (R$)",
        f"R$ {total_vl:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    )

    st.subheader(f"{modo} ➔ {filtro_descr}")

    # --- Tabela principal ---
    df_display = df_resumo.copy()
    df_display["Valor total"] = df_display["Valor total"].apply(
        lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    )
    st.dataframe(df_display, use_container_width=True)

    # --- Previsão de vendas (últimos 15 dias) ---
    if modo == "Últimos 15 dias":
        gerar_tabela_previsao(df, df_resumo)

    # --- Curva ABC Top 15 ---
    gerar_curva_abc(df_resumo)


def gerar_tabela_previsao(df, df_resumo):
    """Tabela de previsão de vendas 7 e 15 dias."""
    today = pd.to_datetime("today").date()

    df15 = df_resumo[["Produto", "Quantidade"]].rename(
        columns={"Quantidade": "Quantidade 15 dias"}
    )

    start7 = pd.to_datetime(today - pd.Timedelta(days=7))
    mask7 = (df["Data da venda"] >= start7) & (df["Data da venda"] <= pd.to_datetime(today))
    df7 = df[mask7]
    df7_sum = (
        df7.groupby("Produto", as_index=False)
        .agg({"Quantidade": "sum"})
        .rename(columns={"Quantidade": "Quantidade 7 dias"})
    )

    df_prev = pd.merge(df15, df7_sum, on="Produto", how="outer").fillna(0)
    df_prev["Quantidade 15 dias"] = df_prev["Quantidade 15 dias"].astype(int)
    df_prev["Quantidade 7 dias"] = df_prev["Quantidade 7 dias"].astype(int)

    df_prev["Estimativa 30 dias (base 7)"] = (df_prev["Quantidade 7 dias"] / 7 * 30).round().astype(int)
    df_prev["Estimativa 30 dias (base 15)"] = (df_prev["Quantidade 15 dias"] / 15 * 30).round().astype(int)

    df_prev = df_prev.sort_values("Quantidade 15 dias", ascending=False)

    st.subheader("Previsão de Vendas — 7 e 15 dias")
    st.dataframe(df_prev, use_container_width=True)


def gerar_curva_abc(df_resumo):
    """Gera gráfico de Curva ABC Top 15."""
    top15 = df_resumo.head(15).copy()
    top15["Acumulado"] = top15["Valor total"].cumsum()
    total15 = top15["Valor total"].sum()
    top15["% Acumulado"] = (top15["Acumulado"] / total15 * 100).round(2)
    top15["Produto"] = pd.Categorical(
        top15["Produto"], categories=top15["Produto"].tolist(), ordered=True
    )
    fig = px.line(
        top15, x="Produto", y="% Acumulado", markers=True,
        title="Curva ABC (Top 15 Produtos)",
        category_orders={"Produto": top15["Produto"].tolist()}
    )
    fig.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig, use_container_width=True)
