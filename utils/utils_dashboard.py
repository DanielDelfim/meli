import pandas as pd
import json
import streamlit as st
from datetime import datetime, timedelta

def carregar_json_para_df(caminho_json: str) -> pd.DataFrame:
    try:
        with open(caminho_json, "r", encoding="utf-8") as f:
            vendas_raw = json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"❌ Arquivo {caminho_json} não encontrado!")

    vendas = []
    for pedido in vendas_raw:
        data = pedido.get("date_created")
        if not data:
            continue
        for item in pedido.get("order_items", []):
            vendas.append({
                "Data da venda": data,
                "Produto": item["item"]["title"],
                "Quantidade": item["quantity"],
                "Valor total": item["unit_price"] * item["quantity"]
            })

    df = pd.DataFrame(vendas)
    if df.empty:
        return df

    df["Data da venda"] = pd.to_datetime(df["Data da venda"], utc=True, errors="coerce").dt.tz_convert("America/Sao_Paulo")
    df["Data da venda"] = df["Data da venda"].dt.tz_localize(None)
    df["period"] = df["Data da venda"].dt.to_period("M")
    return df


def preparar_periodos(df):
    month_map = {
        1:"Janeiro",2:"Fevereiro",3:"Março",4:"Abril",
        5:"Maio",6:"Junho",7:"Julho",8:"Agosto",
        9:"Setembro",10:"Outubro",11:"Novembro",12:"Dezembro"
    }
    labels = [f"{month_map[p.month]} {p.year}" for p in sorted(df["period"].unique())]
    label_map = {p: f"{month_map[p.month]} {p.year}" for p in df["period"].unique()}
    return labels, label_map


def aplicar_filtro(df, modo, titulo=None):
    mask = pd.Series(True, index=df.index)
    filtro_descr = ""

    if modo == "Diário":
        st.sidebar.header(f"Filtro Diário — {titulo}" if titulo else "Filtro Diário")
        min_date = df["Data da venda"].min().date()
        max_date = df["Data da venda"].max().date()
        today = datetime.today().date()

        start_date = st.sidebar.date_input("Data inicial", value=today, min_value=min_date, max_value=max_date, key=f"start_{titulo}")
        end_date = st.sidebar.date_input("Data final", value=today, min_value=min_date, max_value=max_date, key=f"end_{titulo}")

        start_dt = pd.to_datetime(start_date)
        end_dt = pd.to_datetime(end_date) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
        mask = (df["Data da venda"] >= start_dt) & (df["Data da venda"] <= end_dt)
        filtro_descr = f"{start_dt.strftime('%d/%m/%y')} → {end_dt.strftime('%d/%m/%y')}"

    elif modo == "Últimos 15 dias":
        today = datetime.today().date()
        start15 = pd.to_datetime(today - timedelta(days=15))
        end15 = pd.to_datetime(today)
        mask = (df["Data da venda"] >= start15) & (df["Data da venda"] <= end15)
        filtro_descr = f"Últimos 15 dias ({start15.strftime('%d/%m/%y')} – {end15.strftime('%d/%m/%y')})"

    return mask, filtro_descr


def render_dashboard(titulo, json_path, start_date=None, end_date=None):
    st.subheader(titulo)

    df = carregar_json_para_df(json_path)
    if df.empty:
        st.warning("Nenhuma venda encontrada.")
        return

    # Aplica o filtro diário caso datas sejam passadas
    if start_date and end_date:
        start_dt = pd.to_datetime(start_date)
        end_dt = pd.to_datetime(end_date) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
        mask = (df["Data da venda"] >= start_dt) & (df["Data da venda"] <= end_dt)
        df = df[mask]

    # Resto da lógica de resumo
    df_resumo = (
        df.groupby("Produto", as_index=False)
        .agg({"Quantidade": "sum", "Valor total": "sum"})
        .sort_values("Valor total", ascending=False)
    )

    total_qt = int(df["Quantidade"].sum())
    total_vl = df["Valor total"].sum()
    col1, col2 = st.columns(2)
    col1.metric("Itens vendidos", total_qt)
    col2.metric("Faturamento (R$)", f"R$ {total_vl:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

    st.dataframe(df_resumo, use_container_width=True)
