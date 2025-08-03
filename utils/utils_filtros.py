import pandas as pd
import json
from datetime import date, datetime

def filtrar_vendas_json_por_periodo(
    caminho_json: str,
    data_inicio,
    data_fim,
    unidade: str = None
) -> pd.DataFrame:
    try:
        with open(caminho_json, "r", encoding="utf-8") as f:
            vendas = json.load(f)
        df = pd.DataFrame(vendas)
    except (FileNotFoundError, json.JSONDecodeError):
        return pd.DataFrame()

    if df.empty or "Data da venda" not in df.columns:
        return pd.DataFrame()

    # Converte mesmo se já estiver formatado
    df["Data da venda"] = pd.to_datetime(df["Data da venda"], errors="coerce")
    df = df.dropna(subset=["Data da venda"])

    # Aplica filtro por intervalo de data
    df_filtrado = df[
        (df["Data da venda"].dt.date >= data_inicio) &
        (df["Data da venda"].dt.date <= data_fim)
    ].copy()

    if unidade and "Unidade" in df_filtrado.columns:
        df_filtrado = df_filtrado[df_filtrado["Unidade"] == unidade]

    # Conversões de segurança
    df_filtrado["Valor total"] = pd.to_numeric(df_filtrado.get("Valor total", 0.0), errors="coerce").fillna(0.0)
    df_filtrado["Quantidade"] = pd.to_numeric(df_filtrado.get("Quantidade", 0), errors="coerce").fillna(0).astype(int)
    df_filtrado["codigo_do_anuncio"] = df_filtrado.get("codigo_do_anuncio", "")
    df_filtrado["Produto"] = df_filtrado.get("Produto", "")

    return df_filtrado
