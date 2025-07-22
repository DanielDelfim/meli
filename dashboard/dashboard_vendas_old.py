import streamlit as st
from datetime import datetime, timedelta
import pandas as pd
import json

st.set_page_config(page_title="Dashboard de Vendas", layout="wide")

@st.cache_data
def load_data():
    try:
        with open(
            "C:/Users/dmdel/OneDrive/Aplicativos/backup_vendas.json",
            "r", encoding="utf-8"
        ) as f:
            vendas = json.load(f)
    except FileNotFoundError:
        st.error("❌ Arquivo 'backup_vendas.json' não encontrado!")
        return pd.DataFrame()
    df = pd.DataFrame(vendas)
    df["Data da venda"] = pd.to_datetime(df["Data da venda"], errors="coerce")
    df["period"] = df["Data da venda"].dt.to_period("M")
    month_map = {
        1:"Janeiro",2:"Fevereiro",3:"Março",4:"Abril",
        5:"Maio",6:"Junho",7:"Julho",8:"Agosto",
        9:"Setembro",10:"Outubro",11:"Novembro",12:"Dezembro"
    }
    df["Mês/Ano"] = df["period"].apply(lambda p: f"{month_map[p.month]} {p.year}")
    return df

df = load_data()
st.title("📊 Dashboard de Vendas Consolidadas")

if df.empty:
    st.warning("Nenhum dado carregado.")
    st.stop()

# --- Escolha do modo de filtro ---
st.sidebar.header("Modo de Filtro")
modo = st.sidebar.radio("Filtrar por:", ["Diário", "Mensal", "Últimos 15 dias"])

# Preparação de valores
min_date = df["Data da venda"].min().date()
max_date = df["Data da venda"].max().date()
periods = sorted(df["period"].unique())
label_map = {p: df.loc[df["period"]==p, "Mês/Ano"].iloc[0] for p in periods}
labels = [label_map[p] for p in periods]

# Inicializa a máscara como toda a base
mask = pd.Series(True, index=df.index)
filtro_descr = ""

if modo == "Diário":
    st.sidebar.header("Filtro Diário")
    start_date = st.sidebar.date_input("Data inicial", value=min_date)
    end_date   = st.sidebar.date_input("Data final",   value=max_date)
    start_dt = pd.to_datetime(start_date)
    end_dt   = pd.to_datetime(end_date)
    mask = (df["Data da venda"] >= start_dt) & (df["Data da venda"] <= end_dt)
    filtro_descr = f"{start_dt.strftime('%d/%m/%Y')} → {end_dt.strftime('%d/%m/%Y')}"

elif modo == "Mensal":
    st.sidebar.header("Filtro Mensal")
    selecionados = st.sidebar.multiselect("Mês/Ano", labels, default=labels)
    if not selecionados:
        selecionados = labels
    selected_periods = [p for p, lbl in label_map.items() if lbl in selecionados]
    mask = df["period"].isin(selected_periods)
    filtro_descr = ", ".join(selecionados)

else:  # Últimos 15 dias
    today = datetime.today().date()
    start_15 = today - timedelta(days=15)
    start_dt = pd.to_datetime(start_15)
    end_dt   = pd.to_datetime(today)
    mask = (df["Data da venda"] >= start_dt) & (df["Data da venda"] <= end_dt)
    filtro_descr = f"Últimos 15 dias ({start_dt.strftime('%d/%m/%Y')} – {end_dt.strftime('%d/%m/%Y')})"

# Aplica o filtro escolhido
dff = df[mask]

# Consolida por produto e ordena
df_resumo = (
    dff.groupby("Produto", as_index=False)
       .agg({"Quantidade":"sum","Valor total":"sum"})
       .sort_values("Valor total", ascending=False)
)

# --- Consolida por produto e ordena (NUMÉRICO) ---
df_resumo = (
    dff.groupby("Produto", as_index=False)
       .agg({"Quantidade":"sum","Valor total":"sum"})
       .sort_values("Valor total", ascending=False)
)

# --- Métricas resumidas (ainda usando números) ---
total_fat = df_resumo["Valor total"].sum()
qtd_total  = int(dff["Quantidade"].sum())

col1, col2 = st.columns(2)
col1.metric("Itens vendidos", qtd_total)
# formata só a string do card
col2.metric("Faturamento Total", f"R$ {total_fat:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

# --- Prepara um DataFrame só para EXIBIÇÃO com string formatada ---
df_display = df_resumo.copy()
df_display["Valor total"] = (
    df_display["Valor total"]
      .apply(lambda x: f"R$ {x:,.2f}")
      .str.replace(",", "X")
      .str.replace(".", ",")
      .str.replace("X", ".")
)

# --- Exibe a tabela formatada (sem quebrar os numéricos originais) ---
st.subheader("Resumo Consolidado por Produto")
st.dataframe(df_display, use_container_width=True)

# … depois de st.dataframe(df_resumo, use_container_width=True)

# Se estivermos em "Últimos 15 dias", mostra a previsão
if modo == "Últimos 15 dias":
    # Cria um DataFrame com Produto e Quantidade
    df_previsao = df_resumo[["Produto", "Quantidade"]].copy()
    # Insere a coluna de previsão (quantidade * 2)
    df_previsao["Previsão próximos 30 dias"] = df_previsao["Quantidade"] * 2

    st.subheader("Previsão de vendas para próximos 30 dias")
    st.dataframe(df_previsao, use_container_width=True)

# --- Curva ABC Top 15 corrigida ---
top15 = df_resumo.head(15).copy()
top15["Acumulado"]    = top15["Valor total"].cumsum()
total15               = top15["Valor total"].sum()
top15["% Acumulado"]  = (top15["Acumulado"] / total15 * 100).round(2)

# fixa ordem dos produtos
top15["Produto"] = pd.Categorical(
    top15["Produto"],
    categories=top15["Produto"].tolist(),
    ordered=True
)

# plota com Plotly Express
import plotly.express as px
fig = px.line(
    top15,
    x="Produto",
    y="% Acumulado",
    markers=True,
    title="Curva ABC (Top 15 Produtos)",
    category_orders={"Produto": top15["Produto"].tolist()}
)
fig.update_layout(xaxis_tickangle=-45)
st.plotly_chart(fig, use_container_width=True)
