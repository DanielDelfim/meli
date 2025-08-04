import streamlit as st
import pandas as pd
import math
from datetime import datetime, timedelta
from utils.utils_filtros import filtrar_vendas_json_por_periodo

def gerar_previsao_30d(dff):
    hoje = datetime.now().date()
    start_15d = hoje - timedelta(days=15)
    start_7d = hoje - timedelta(days=7)

    dff["Data da venda"] = pd.to_datetime(dff["Data da venda"], errors="coerce").dt.date

    df_15 = dff[dff["Data da venda"] >= start_15d].groupby(["Unidade", "Produto"], as_index=False).agg({"Quantidade": "sum"})
    df_15.rename(columns={"Quantidade": "Qtd 15d"}, inplace=True)

    df_7 = dff[dff["Data da venda"] >= start_7d].groupby(["Unidade", "Produto"], as_index=False).agg({"Quantidade": "sum"})
    df_7.rename(columns={"Quantidade": "Qtd 7d"}, inplace=True)

    prev = pd.merge(df_15, df_7, on=["Unidade", "Produto"], how="outer").fillna(0)
    prev["Est30d_15d"] = (prev["Qtd 15d"] / 15 * 30).round().astype(int)
    prev["Est30d_7d"] = (prev["Qtd 7d"] / 7 * 30).round().astype(int)

    return prev.sort_values("Est30d_15d", ascending=False)

def render_dashboard(titulo, json_sp=None, json_mg=None):
    st.title(f"📊 Dashboard de Vendas — {titulo}")

    col1, col2 = st.columns(2)
    hoje = datetime.now().date()
    data_inicio = col1.date_input("🗕️ Data inicial", value=hoje - timedelta(days=30), key="data_ini")
    data_fim = col2.date_input("🗕️ Data final", value=hoje, key="data_fim")

    df_sp = filtrar_vendas_json_por_periodo(json_sp, data_inicio, data_fim, unidade="SP") if json_sp else pd.DataFrame()
    df_mg = filtrar_vendas_json_por_periodo(json_mg, data_inicio, data_fim, unidade="MG") if json_mg else pd.DataFrame()
    df = pd.concat([df_sp, df_mg], ignore_index=True)

    if df.empty:
        st.warning("❌ Nenhum dado encontrado no período selecionado.")
        return

    lista_produtos = sorted(df["Produto"].dropna().unique().tolist())
    produto_selecionado = st.selectbox(
        "🔎 Filtrar por produto (opcional)",
        options=[""] + lista_produtos,
        index=0,
        key=f"produto_busca_{titulo}"
    )

    dff = df[df["Produto"] == produto_selecionado] if produto_selecionado else df

    dff["Data da venda"] = pd.to_datetime(dff["Data da venda"], errors="coerce").dt.date

    total_qt = int(dff["Quantidade"].sum())
    total_vl = dff["Valor total"].sum()

    c1, c2 = st.columns(2)
    c1.metric("Itens vendidos", total_qt)
    c2.metric("Faturamento (R$)", f"R$ {total_vl:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

    st.subheader("📦 Resumo de vendas")
    resumo = (
        dff.groupby(["Unidade", "Produto"], as_index=False)
        .agg({"Quantidade": "sum", "Valor total": "sum"})
        .sort_values("Valor total", ascending=False)
    )
    st.dataframe(resumo, use_container_width=True)

    st.subheader("📈 Previsão de Vendas para 30 dias (baseada em 7 e 15 dias)")
    previsao = gerar_previsao_30d(dff)
    if not previsao.empty:
        st.dataframe(previsao, use_container_width=True)
    else:
        st.info("Sem dados suficientes para gerar previsão.")

     # ---------------------- ESTOQUE MANUAL E ESTIMATIVAS ----------------------
    if produto_selecionado:
        st.subheader("📦 Estimativa de Estoque")

        col1, col2 = st.columns(2)
        estoque_atual = col1.number_input(
            "Estoque atual (unidades)",
            min_value=0,
            step=1,
            value=0,
            key=f"estoque_atual_{produto_selecionado}"
        )

        dias_futuros = col2.number_input(
            "Projeção em X dias",
            min_value=1,
            step=1,
            value=30,
            key=f"dias_futuros_{produto_selecionado}"
        )

        # Obter quantidade vendida nos últimos 7 dias
        hoje = datetime.now().date()
        data_7d = hoje - timedelta(days=7)
        vendas_7d = dff[dff["Data da venda"] >= data_7d]["Quantidade"].sum()
        media_diaria = vendas_7d / 7 if vendas_7d > 0 else 0

        # Calcular dias até acabar o estoque
        dias_estoque = math.floor(estoque_atual / media_diaria) if media_diaria > 0 else "∞"

        # Calcular quanto teremos de estoque em X dias
        consumo_previsto = math.floor(media_diaria * dias_futuros)
        estoque_futuro = max(estoque_atual - consumo_previsto, 0)

        # Estimativa de vendas em 30 dias com base nos últimos 7 dias
        estimativa_30_dias = math.floor(media_diaria * 30)

        # Cálculo da quantidade para reposição
        reposicao = max(estimativa_30_dias - estoque_futuro, 0)

        st.markdown("### 📊 Resultados")
        col3, col4, col5 = st.columns(3)
        col3.metric("Dias estimados até o fim do estoque", dias_estoque)
        col4.metric(f"Estoque em {dias_futuros} dias", f"{estoque_futuro} un.")
        col5.metric("Reposição necessária (para 30 dias)", f"{reposicao} un.")

