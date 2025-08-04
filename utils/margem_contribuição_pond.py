import json
import pandas as pd
from datetime import date
from pathlib import Path

def calcular_margem_ponderada(
    df_precos: pd.DataFrame,
    json_path: str,
    start_date: date = None,
    end_date: date = None
) -> float:
    """
    Calcula a Margem de Contribuição Ponderada com base nas vendas
    agregadas por SKU e nas margens definidas por produto.

    Parâmetros:
    - df_precos: DataFrame com colunas 'SKU' e '% Margem de contribuição'
    - json_path: caminho do arquivo de vendas (pré-processado com SKU e Valor total)
    - start_date, end_date: intervalo de datas para filtrar vendas

    Retorna:
    - Float com a margem ponderada (%)
    """

    # Verifica colunas essenciais na precificação
    if "SKU" not in df_precos.columns or "% Margem de contribuição" not in df_precos.columns:
        print("[ERRO] df_precos não contém colunas SKU e/ou % Margem de contribuição")
        return 0.0

    # Remove SKUs duplicados, mantendo o de maior margem
    df_prec = (
        df_precos
        .sort_values("% Margem de contribuição", ascending=False)
        .drop_duplicates(subset="SKU", keep="first")
        .loc[:, ["SKU", "% Margem de contribuição"]]
    )

    if df_prec.empty:
        print("[DEBUG] Sem produtos de precificação após deduplicar por SKU.")
        return 0.0

    # Carrega JSON de vendas
    try:
        with open(json_path, encoding="utf-8") as f:
            vendas = json.load(f)
    except Exception as e:
        print(f"[ERRO] Não foi possível ler {json_path}: {e}")
        return 0.0

    df_sales = pd.DataFrame(vendas)

    if df_sales.empty or "SKU" not in df_sales.columns or "Valor total" not in df_sales.columns:
        print(f"[DEBUG] df_sales vazio ou sem colunas SKU/Valor total em {json_path}")
        return 0.0

    # Converte datas e aplica filtro por período
    df_sales["Data da venda"] = pd.to_datetime(df_sales["Data da venda"], errors="coerce")
    if start_date and end_date:
        df_sales = df_sales[
            (df_sales["Data da venda"].dt.date >= start_date) &
            (df_sales["Data da venda"].dt.date <= end_date)
        ]

    if df_sales.empty:
        print(f"[DEBUG] Sem vendas no período {start_date} → {end_date}")
        return 0.0

    # Agrupa vendas por SKU
    sales_by_sku = (
        df_sales
        .groupby("SKU", as_index=False)["Valor total"]
        .sum()
        .rename(columns={"Valor total": "Total Vendas"})
    )

    total_vendas = sales_by_sku["Total Vendas"].sum()
    if total_vendas == 0:
        print("[DEBUG] Total de vendas no período é zero.")
        return 0.0

    # Merge vendas x margens
    merged = sales_by_sku.merge(df_prec, on="SKU", how="left")

    # Cálculo ponderado
    merged["Peso"] = merged["Total Vendas"] / total_vendas
    merged["Contribuição"] = merged["Peso"] * merged["% Margem de contribuição"]

    # Debug opcional: mostra os 10 principais SKUs por venda
    print(f"[DEBUG] --- MCP Detalhado {start_date} → {end_date} ---")
    print(merged.sort_values("Total Vendas", ascending=False).head(10).to_string(index=False))

    # Retorno final
    mcp = merged["Contribuição"].sum()
    print(f"[DEBUG] MCP final: {mcp:.4f}")
    return float(mcp)
