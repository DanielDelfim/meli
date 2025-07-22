import pandas as pd
from datetime import timedelta

def carregar_json_para_df(path_json: str) -> pd.DataFrame:
    """
    Lê um arquivo JSON de vendas (pedidos) do Mercado Livre e
    retorna um DataFrame com as colunas:
    - Data da venda
    - Produto
    - Quantidade
    - Valor total
    """
    import json
    try:
        with open(path_json, "r", encoding="utf-8") as f:
            vendas_raw = json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"❌ Arquivo '{path_json}' não encontrado!")

    linhas = []
    for pedido in vendas_raw:
        data = pedido.get("date_created")
        if not data:
            continue
        for item in pedido.get("order_items", []):
            linhas.append({
                "Data da venda": data,
                "Produto": item.get("item", {}).get("title", "Produto sem nome"),
                "Quantidade": item.get("quantity", 0),
                "Valor total": item.get("quantity", 0) * item.get("unit_price", 0)
            })

    if not linhas:
        return pd.DataFrame()

    df = pd.DataFrame(linhas)
    return ajustar_datas(df)


def ajustar_datas(df: pd.DataFrame) -> pd.DataFrame:
    """
    Converte a coluna 'Data da venda' para datetime com timezone
    America/Sao_Paulo e remove o timezone para facilitar comparações.
    """
    df["Data da venda"] = (
        pd.to_datetime(df["Data da venda"], utc=True, errors="coerce")
        .dt.tz_convert("America/Sao_Paulo")
    )
    df["Data da venda"] = df["Data da venda"].dt.tz_localize(None)
    df["period"] = df["Data da venda"].dt.to_period("M")
    return df


def preparar_periodos(df: pd.DataFrame):
    """
    Adiciona a coluna 'Mês/Ano' ao DataFrame e retorna o mapeamento de labels.
    """
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


def aplicar_filtro(df: pd.DataFrame, modo: str, start_date=None, end_date=None):
    """
    Aplica filtros de data conforme o modo selecionado:
    - "Diário"
    - "Mensal"
    - "Últimos 15 dias"
    """
    from datetime import datetime

    mask = pd.Series(True, index=df.index)
    filtro_descr = ""

    if modo == "Diário":
        if start_date is None:
            start_date = df["Data da venda"].min().date()
        if end_date is None:
            end_date = df["Data da venda"].max().date()
        start_dt = pd.to_datetime(start_date)
        end_dt = pd.to_datetime(end_date) + timedelta(days=1) - timedelta(seconds=1)
        mask = (df["Data da venda"] >= start_dt) & (df["Data da venda"] <= end_dt)
        filtro_descr = f"{start_dt.strftime('%d/%m/%Y')} → {end_dt.strftime('%d/%m/%Y')}"

    elif modo == "Mensal":
        # Filtro mensal é tratado externamente usando periods
        filtro_descr = "Filtro Mensal aplicado"

    elif modo == "Últimos 15 dias":
        today = datetime.today().date()
        start15 = pd.to_datetime(today - timedelta(days=15))
        end15 = pd.to_datetime(today) + timedelta(days=1) - timedelta(seconds=1)
        mask = (df["Data da venda"] >= start15) & (df["Data da venda"] <= end15)
        filtro_descr = f"Últimos 15 dias ({start15.strftime('%d/%m/%Y')} – {end15.strftime('%d/%m/%Y')})"

    return mask, filtro_descr
