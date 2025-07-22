import streamlit as st
import pandas as pd
import json
from datetime import datetime, timedelta
import os

BASE_PATH = r"C:/Users/dmdel/OneDrive/Aplicativos"
DESIGNER_PATH = os.path.join(BASE_PATH, "Designer")

# --- Função para carregar JSON ---

def carregar_json_para_df(json_path: str) -> pd.DataFrame:
    """
    Carrega um arquivo JSON de vendas do Mercado Livre e retorna como DataFrame.
    Adiciona uma coluna 'codigo_do_anuncio' extraída de order_items[0]['item']['id'].
    """

    if not os.path.exists(json_path):
        raise FileNotFoundError(f"Arquivo não encontrado: {json_path}")

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        data = [data]

    df = pd.DataFrame(data)

    # --- Extrair Data da venda ---
    if "date_created" in df.columns:
        df["Data da venda"] = pd.to_datetime(df["date_created"], errors="coerce")
    elif "Data da venda" not in df.columns:
        df["Data da venda"] = pd.NaT

    # --- Extrair código do anúncio ---
    def extrair_codigo(order_items):
        try:
            if isinstance(order_items, list) and len(order_items) > 0:
                return order_items[0].get("item", {}).get("id", None)
            return None
        except Exception:
            return None

    if "order_items" in df.columns:
        df["codigo_do_anuncio"] = df["order_items"].apply(extrair_codigo)
    else:
        df["codigo_do_anuncio"] = None

    # --- Valor total da venda ---
    if "total_amount" in df.columns:
        df["Valor total"] = pd.to_numeric(df["total_amount"], errors="coerce").fillna(0)
    else:
        df["Valor total"] = 0

    # --- Quantidade de itens vendidos ---
    def extrair_quantidade(order_items):
        try:
            if isinstance(order_items, list) and len(order_items) > 0:
                return order_items[0].get("quantity", 1)
            return 1
        except Exception:
            return 1

    if "order_items" in df.columns:
        df["Quantidade"] = df["order_items"].apply(extrair_quantidade)
    else:
        df["Quantidade"] = 1

    # --- Produto (Título) ---
    def extrair_titulo(order_items):
        try:
            if isinstance(order_items, list) and len(order_items) > 0:
                return order_items[0].get("item", {}).get("title", "Produto desconhecido")
            return "Produto desconhecido"
        except Exception:
            return "Produto desconhecido"

    if "order_items" in df.columns:
        df["Produto"] = df["order_items"].apply(extrair_titulo)
    else:
        df["Produto"] = "Produto desconhecido"

    return df

# --- Preparar períodos (para Mensal) ---
def preparar_periodos(df):
    month_map = {
        1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
        5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
        9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
    }
    df["Mês/Ano"] = df["period"].apply(lambda p: f"{month_map[p.month]} {p.year}")
    periods = sorted(df["period"].unique())
    label_map = {p: df.loc[df["period"] == p, "Mês/Ano"].iloc[0] for p in periods}
    labels = [label_map[p] for p in periods]
    return labels, label_map


# --- Aplicar filtro ---
def aplicar_filtro(df, modo):
    mask = pd.Series(True, index=df.index)
    filtro_descr = ""

    if modo == "Diário":
        st.sidebar.header("Filtro Diário")
        first_day = datetime.today().replace(day=1).date()
        today = datetime.today().date()

        start_date = st.sidebar.date_input("Data inicial", value=first_day)
        end_date = st.sidebar.date_input("Data final", value=today)

        start_dt = pd.to_datetime(start_date)
        end_dt = pd.to_datetime(end_date) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)

        mask = (df["Data da venda"] >= start_dt) & (df["Data da venda"] <= end_dt)
        filtro_descr = f"{start_dt.strftime('%d/%m/%y')} → {end_dt.strftime('%d/%m/%y')}"

    elif modo == "Mensal":
        st.sidebar.header("Filtro Mensal")
        labels, label_map = preparar_periodos(df)
        selecionados = st.sidebar.multiselect("Mês/Ano", options=labels, default=labels)
        sel_periods = [p for p, lbl in label_map.items() if lbl in selecionados]
        mask = df["period"].isin(sel_periods)
        filtro_descr = ", ".join(selecionados)

    elif modo == "Últimos 15 dias":
        today = datetime.today().date()
        start15 = pd.to_datetime(today - timedelta(days=15))
        end15 = pd.to_datetime(today)
        mask = (df["Data da venda"] >= start15) & (df["Data da venda"] <= end15)
        filtro_descr = f"Últimos 15 dias ({start15.strftime('%d/%m/%y')} – {end15.strftime('%d/%m/%y')})"

    return mask, filtro_descr


# --- Renderizar dashboard ---
def render_dashboard(titulo, json_path):
    try:
        df = carregar_json_para_df(json_path)
    except FileNotFoundError as e:
        st.error(str(e))
        return

    if df.empty:
        st.warning("Nenhuma venda encontrada no JSON.")
        return

    modo = st.sidebar.radio(f"Filtrar por ({titulo})", ["Diário", "Mensal", "Últimos 15 dias"])
    mask, filtro_descr = aplicar_filtro(df, modo)
    dff = df[mask]

    if dff.empty:
        st.warning(f"Nenhuma venda encontrada no período selecionado para {titulo}.")
        return

    df_resumo = (
        dff.groupby("Produto", as_index=False)
        .agg({"Quantidade": "sum", "Valor total": "sum"})
        .sort_values("Valor total", ascending=False)
    )

    total_qt = int(dff["Quantidade"].sum())
    total_vl = dff["Valor total"].sum()
    col1, col2 = st.columns(2)
    col1.metric("Itens vendidos", total_qt)
    col2.metric("Faturamento (R$)", f"R$ {total_vl:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

    st.subheader(f"{modo} ➔ {filtro_descr}")
    st.dataframe(df_resumo, use_container_width=True)
