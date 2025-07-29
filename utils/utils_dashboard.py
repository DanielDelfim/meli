import json
import pandas as pd
from datetime import timedelta
from pathlib import Path
import pytz

# Timezone de Brasília
TZ = pytz.timezone("America/Sao_Paulo")

# ------------------- Funções de extração -------------------
def extrair_produto(item):
    """Extrai título do produto a partir da estrutura do order_items."""
    if "item" in item:
        return item.get("item", {}).get("title", "Produto não identificado")
    return item.get("title", "Produto não identificado")

def extrair_quantidade(item):
    """Extrai a quantidade do produto."""
    return item.get("quantity", 0)

def extrair_valor(item):
    """Calcula o valor total do item."""
    qtd = item.get("quantity", 0)
    preco = item.get("unit_price", 0)
    return qtd * preco

# ------------------- Carregamento de JSON -------------------
import json
import pandas as pd
from zoneinfo import ZoneInfo

TZ = ZoneInfo("America/Sao_Paulo")

def carregar_json_para_df(caminho_json: str) -> pd.DataFrame:
    """
    Lê um JSON pré-processado e retorna DataFrame pronto.
    As datas já estão ajustadas no arquivo .json pelo preprocess.
    """
    try:
        with open(caminho_json, "r", encoding="utf-8") as f:
            vendas_raw = json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"❌ Arquivo {caminho_json} não encontrado!")

    df = pd.DataFrame(vendas_raw)
    if "Data da venda" in df.columns:
        df["Data da venda"] = pd.to_datetime(df["Data da venda"], errors="coerce")

    return df

# ------------------- Períodos -------------------
def preparar_periodos(df: pd.DataFrame):
    """
    Prepara labels de período (mensal) para filtros.
    """
    month_map = {
        1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
        5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
        9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
    }
    labels = []
    label_map = {}
    for p in sorted(df["period"].unique()):
        label = f"{month_map[p.month]} {p.year}"
        labels.append(label)
        label_map[p] = label
    return labels, label_map

# ------------------- Filtros -------------------
def aplicar_filtro(df: pd.DataFrame, modo: str, data_inicio=None, data_fim=None):
    """
    Aplica filtro diário, mensal ou últimos 15 dias.
    """
    if df.empty:
        return df, ""

    if modo == "Diário" and data_inicio and data_fim:
        start_dt = pd.to_datetime(f"{data_inicio} 00:00:00")
        end_dt = pd.to_datetime(f"{data_fim} 23:59:59")
        mask = (df["Data da venda"] >= start_dt) & (df["Data da venda"] <= end_dt)
        desc = f"{start_dt.strftime('%d/%m/%y')} → {end_dt.strftime('%d/%m/%y')}"
        return df[mask], desc

    elif modo == "Últimos 15 dias":
        end_dt = df["Data da venda"].max()
        start_dt = end_dt - timedelta(days=15)
        mask = (df["Data da venda"] >= start_dt) & (df["Data da venda"] <= end_dt)
        desc = f"Últimos 15 dias ({start_dt.strftime('%d/%m/%y')} – {end_dt.strftime('%d/%m/%y')})"
        return df[mask], desc

    elif modo == "Mensal":
        # Sem data de início/fim, retorna tudo agrupado por período
        desc = "Filtro Mensal"
        return df, desc

    return df, "Todos os dados"
