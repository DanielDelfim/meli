import streamlit as st
import pandas as pd
import json
from datetime import datetime, timedelta
import os
from zoneinfo import ZoneInfo

TZ = ZoneInfo("America/Sao_Paulo")

BASE_PATH = r"C:/Users/dmdel/OneDrive/Aplicativos"
DESIGNER_PATH = os.path.join(BASE_PATH, "Designer")

# --- Função para carregar JSON ---

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
                "Valor total": item["unit_price"] * item["quantity"],
                "order_items": pedido.get("order_items", []),
                "total_amount": pedido.get("total_amount", 0)
            })

    df = pd.DataFrame(vendas)
    if df.empty:
        return df

    # ---- Timezone: mantém tz-aware em America/Sao_Paulo ----
    df["Data da venda"] = (
        pd.to_datetime(df["Data da venda"], utc=True, errors="coerce")
          .dt.tz_convert(TZ)
    )

    # period funciona com tz-aware também
    df["period"] = df["Data da venda"].dt.to_period("M")

    # --- Extrair código / quantidade / título / valor ---
    df["codigo_do_anuncio"] = df.get("order_items", None).apply(extrair_codigo)
    df["Quantidade"] = df.get("order_items", None).apply(extrair_quantidade)
    df["Produto"] = df.get("order_items", None).apply(extrair_titulo)
    df["Valor total"] = pd.to_numeric(df.get("total_amount", 0), errors="coerce").fillna(0)

    return df

# --- Extrair código do anúncio ---
def extrair_codigo(order_items):
    try:
        if isinstance(order_items, list) and len(order_items) > 0:
            return order_items[0].get("item", {}).get("id", None)
        return None
    except Exception:
        return None

# --- Quantidade de itens vendidos ---
def extrair_quantidade(order_items):
    try:
        if isinstance(order_items, list) and len(order_items) > 0:
            return order_items[0].get("quantity", 1)
        return 1
    except Exception:
        return 1

# --- Produto (Título) ---
def extrair_titulo(order_items):
    try:
        if isinstance(order_items, list) and len(order_items) > 0:
            return order_items[0].get("item", {}).get("title", "Produto desconhecido")
        return "Produto desconhecido"
    except Exception:
        return "Produto desconhecido"

# Adicione o processamento extra dentro da função carregar_json_para_df
def carregar_json_para_df(caminho_json: str) -> pd.DataFrame:
    import json
    import pandas as pd

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
                "Valor total": item["unit_price"] * item["quantity"],
                "order_items": pedido.get("order_items", []),
                "total_amount": pedido.get("total_amount", 0)
            })

    df = pd.DataFrame(vendas)
    if df.empty:
        return df

    # --- Corrigir timezone ---
    df["Data da venda"] = pd.to_datetime(df["Data da venda"], utc=True, errors="coerce")
    df["Data da venda"] = df["Data da venda"].dt.tz_convert("America/Sao_Paulo")  # Ajusta para SP
    df["Data da venda"] = df["Data da venda"].dt.tz_localize(None)  # Remove o timezone

    df["period"] = df["Data da venda"].dt.to_period("M")

    # --- Extrair código do anúncio ---
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
    if "order_items" in df.columns:
        df["Quantidade"] = df["order_items"].apply(extrair_quantidade)
    else:
        df["Quantidade"] = 1

    # --- Produto (Título) ---
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
def aplicar_filtro(df, modo, titulo=None):
    mask = pd.Series(True, index=df.index)
    filtro_descr = ""

    # Determinar colunas de data (compatível com vendas ou publicidade)
    if "Data da venda" in df.columns:
        col_data = "Data da venda"
    elif "desde" in df.columns:
        col_data = "desde"
    else:
        st.error("❌ Nenhuma coluna de data encontrada no DataFrame.")
        return mask, "Sem período"

    if df[col_data].dt.tz is None:
        df[col_data] = df[col_data].dt.tz_localize(TZ)

    # Obter intervalos mínimo e máximo
    min_date = df[col_data].min().date()
    max_date = df[col_data].max().date()
    today = datetime.today().date()

    if modo == "Diário":
        st.sidebar.header(f"Filtro Diário — {titulo}" if titulo else "Filtro Diário")

        # Datas mín/máx (no tz local)
        min_date = df[col_data].min().astimezone(TZ).date()
        max_date = df[col_data].max().astimezone(TZ).date()
        today = datetime.now(TZ).date()

        default_start = today if min_date <= today <= max_date else min_date
        default_end = today if min_date <= today <= max_date else max_date

        start_date = st.sidebar.date_input("Data inicial", value=default_start,
                                           min_value=min_date, max_value=max_date,
                                           key=f"start_{titulo}")
        end_date = st.sidebar.date_input("Data final", value=default_end,
                                         min_value=min_date, max_value=max_date,
                                         key=f"end_{titulo}")

        start_dt = pd.Timestamp(start_date, tz=TZ)
        end_dt = pd.Timestamp(end_date, tz=TZ) + pd.Timedelta(days=1)

        mask = (df[col_data] >= start_dt) & (df[col_data] < end_dt)
        filtro_descr = f"{start_dt.strftime('%d/%m/%y')} → {(end_dt - pd.Timedelta(seconds=1)).strftime('%d/%m/%y')}"


    elif modo == "Mensal":
        st.sidebar.header(f"Filtro Mensal — {titulo}" if titulo else "Filtro Mensal")
        if "period" not in df.columns:
            df["period"] = df[col_data].dt.to_period("M")
        labels, label_map = preparar_periodos(df)
        selecionados = st.sidebar.multiselect("Mês/Ano", options=labels, default=labels)
        sel_periods = [p for p, lbl in label_map.items() if lbl in selecionados]
        mask = df["period"].isin(sel_periods)
        filtro_descr = ", ".join(selecionados)

    elif modo == "Últimos 15 dias":
        end15 = df[col_data].max()
        start15 = end15 - pd.Timedelta(days=15)
        mask = (df[col_data] >= start15) & (df[col_data] < end15 + pd.Timedelta(days=1))
        filtro_descr = f"Últimos 15 dias ({start15.astimezone(TZ).strftime('%d/%m/%y')} – {end15.astimezone(TZ).strftime('%d/%m/%y')})"

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
