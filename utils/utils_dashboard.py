import json
import os
import pandas as pd
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

# Configurações de fuso e caminhos
TZ = ZoneInfo("America/Sao_Paulo")
BASE_PATH = os.getenv("BASE_PATH", r"C:/Users/dmdel/OneDrive/Aplicativos")
DESIGNER_PATH = os.path.join(BASE_PATH, "Designer")

# --- Funções auxiliares de extração ---

def extrair_codigo(order_items):
    try:
        if isinstance(order_items, list) and order_items:
            return order_items[0].get("item", {}).get("id")
    except Exception:
        pass
    return None


def extrair_quantidade(order_items):
    try:
        if isinstance(order_items, list) and order_items:
            return order_items[0].get("quantity", 0)
    except Exception:
        pass
    return 0


def extrair_titulo(order_items):
    try:
        if isinstance(order_items, list) and order_items:
            return order_items[0].get("item", {}).get("title", "")
    except Exception:
        pass
    return ""

# --- Função principal de carregamento ---
def carregar_json_para_df(caminho_json: str) -> pd.DataFrame:
    """
    Lê um JSON de pedidos no formato ML e retorna DataFrame com colunas:
      Data da venda, Produto, Quantidade, Valor total, order_items, total_amount
    """
    try:
        with open(caminho_json, "r", encoding="utf-8") as f:
            vendas_raw = json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"❌ Arquivo {caminho_json} não encontrado!")

    rows = []
    for pedido in vendas_raw:
        data_utc = pedido.get("date_created")
        if not data_utc:
            continue
        items = pedido.get("order_items", [])
        total_amount = pedido.get("total_amount", 0)
        for it in items:
            rows.append({
                "Data da venda": data_utc,
                "Produto": it.get("item", {}).get("title", ""),
                "Quantidade": it.get("quantity", 0),
                "Valor total": it.get("unit_price", 0) * it.get("quantity", 0),
                "order_items": items,
                "total_amount": total_amount,
            })

    df = pd.DataFrame(rows)
    if df.empty:
        return df

    # Converte UTC para horário de SP e remove tzinfo
    df["Data da venda"] = (
        pd.to_datetime(df["Data da venda"], utc=True, errors="coerce")
          .dt.tz_convert(TZ)
          .dt.tz_localize(None)
    )
    # Período mensal
    df["period"] = df["Data da venda"].dt.to_period("M")

    # Ajusta colunas derivadas
    df["codigo_do_anuncio"] = df["order_items"].apply(extrair_codigo)
    df["Quantidade"] = df["order_items"].apply(extrair_quantidade)
    df["Produto"] = df["order_items"].apply(extrair_titulo)
    df["Valor total"] = pd.to_numeric(df.get("total_amount", 0), errors="coerce").fillna(0)

    return df

# --- Funções de filtro e renderização ---

def preparar_periodos(df: pd.DataFrame):
    month_map = {
        1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
        5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
        9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
    }
    labels = []
    for p in sorted(df["period"].unique()):
        labels.append(f"{month_map[p.month]} {p.year}")
    return labels


def aplicar_filtro(df: pd.DataFrame, modo: str, titulo: str = None):
    """
    Aplica filtro 'Diário', 'Mensal' ou 'Últimos 15 dias' e retorna máscara booleana.
    """
    if modo == "Diário":
        min_date = df["Data da venda"].min().date()
        max_date = df["Data da venda"].max().date()
        start_date = min_date
        end_date = max_date
        mask = (
            df["Data da venda"].dt.date >= start_date) & (
            df["Data da venda"].dt.date <= end_date)
        return mask
    elif modo == "Mensal":
        return df["period"].isin(df["period"].unique())
    elif modo == "Últimos 15 dias":
        end = df["Data da venda"].max()
        start = end - timedelta(days=15)
        return (df["Data da venda"] >= start) & (df["Data da venda"] <= end)
    else:
        return pd.Series(True, index=df.index)

# Não import streamlit aqui para evitar circularidade
