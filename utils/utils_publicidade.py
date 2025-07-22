import os
import json
import pandas as pd
import unicodedata


BASE_PATH = r"C:\Users\dmdel\OneDrive\Aplicativos"
DESIGNER_PATH = os.path.join(BASE_PATH, "Designer")


# ============================================================
# Função para normalizar nomes de colunas
# ============================================================
def normalize_text(text) -> str:
    """Remove acentos e normaliza para minúsculas com underscores."""
    text = str(text)  # garante que é string
    text = unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('ASCII')
    return text.lower().replace(" ", "_").replace("\n", "_")

# ============================================================
# Carregar planilha de publicidade
# ============================================================

def carregar_json_para_df(json_path: str) -> pd.DataFrame:
    """
    Carrega o JSON de vendas e retorna um DataFrame.
    Remove timezone da coluna 'Data da venda', caso exista.
    """
    if not os.path.exists(json_path):
        raise FileNotFoundError(f"Arquivo não encontrado: {json_path}")

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError(f"O arquivo {json_path} não contém uma lista de vendas válida.")

    df = pd.json_normalize(data)

    # Normaliza coluna de datas (remove timezone)
    if "date_created" in df.columns:
        df["Data da venda"] = pd.to_datetime(df["date_created"], errors="coerce").dt.tz_localize(None)
    elif "Data da venda" in df.columns:
        df["Data da venda"] = pd.to_datetime(df["Data da venda"], errors="coerce").dt.tz_localize(None)

    # Renomear colunas importantes, se necessário
    if "total_amount" in df.columns and "Valor total" not in df.columns:
        df.rename(columns={"total_amount": "Valor total"}, inplace=True)

    if "order_items" in df.columns:
        df["Produto"] = df["order_items"].apply(
            lambda x: x[0]["item"]["title"] if isinstance(x, list) and len(x) > 0 else ""
        )

    if "order_items" in df.columns:
        df["Quantidade"] = df["order_items"].apply(
            lambda x: x[0]["quantity"] if isinstance(x, list) and len(x) > 0 else 1
        )

    return df

# ============================================================
# Carregar JSON de vendas
# ============================================================
def carregar_vendas(json_path: str) -> pd.DataFrame:
    """
    Carrega o JSON de vendas e retorna DataFrame com anuncio_id, via_ads e date_created.
    """
    if not os.path.exists(json_path):
        raise FileNotFoundError(f"Arquivo de vendas não encontrado: {json_path}")

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    vendas_list = []
    for venda in data:
        anuncio_id = venda.get("order_items", [{}])[0].get("item", {}).get("id")
        via_ads = venda.get("via_ads", "Não")
        data_venda = venda.get("date_closed") or venda.get("date_created")
        vendas_list.append({
            "anuncio_id": anuncio_id,
            "via_ads": via_ads,
            "date_created": data_venda
        })

    df = pd.DataFrame(vendas_list)
    df["date_created"] = pd.to_datetime(df["date_created"], errors="coerce")

    # Remover timezone, se existir
    if pd.api.types.is_datetime64tz_dtype(df["date_created"]):
        df["date_created"] = df["date_created"].dt.tz_convert(None)

    return df


# ============================================================
# Preparar DataFrame de publicidade com vendas
# ============================================================
def carregar_ads(file_path: str) -> pd.DataFrame:
    """
    Carrega o arquivo de publicidade (CSV, JSON ou XLSX) e retorna um DataFrame.
    """
    import os
    import pandas as pd

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Arquivo de publicidade não encontrado: {file_path}")

    ext = os.path.splitext(file_path)[1].lower()

    if ext in [".csv"]:
        df = pd.read_csv(file_path, skiprows=1)
    elif ext in [".json"]:
        df = pd.read_json(file_path)
    elif ext in [".xls", ".xlsx"]:
        df = pd.read_excel(file_path, skiprows=1)  # Adicionando suporte para Excel
    else:
        raise ValueError("Formato de arquivo de anúncios não suportado. Use CSV, JSON ou XLSX.")

    # Normalização de nomes das colunas
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_").str.replace("__", "_")

    return df

def preparar_dataframe_publicidade(json_path: str, ads_path: str, start_date=None, end_date=None) -> pd.DataFrame:
    """
    Combina dados de publicidade com vendas, aplicando filtro de datas.
    """
    df_ads = carregar_ads(ads_path)
    df_vendas = carregar_vendas(json_path)

    # Filtro por período
    if start_date and end_date:
        start_dt = pd.to_datetime(start_date).tz_localize(None)
        end_dt = pd.to_datetime(end_date).tz_localize(None) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
        df_vendas = df_vendas[
            (df_vendas["date_created"] >= start_dt) & (df_vendas["date_created"] <= end_dt)
        ]

    # Contagem de vendas (Sim / Não)
    vendas_por_anuncio = (
        df_vendas.groupby(["anuncio_id", "via_ads"])
        .size()
        .unstack(fill_value=0)
        .reset_index()
    )

    # Adicionar total_vendas
    colunas_numericas = [c for c in vendas_por_anuncio.columns if c not in ["anuncio_id"]]
    vendas_por_anuncio["total_vendas"] = vendas_por_anuncio[colunas_numericas].sum(axis=1)

    # Garantir que colunas Sim/Não existem
    if "Sim" not in vendas_por_anuncio.columns:
        vendas_por_anuncio["Sim"] = 0
    if "Não" not in vendas_por_anuncio.columns:
        vendas_por_anuncio["Não"] = 0

    # Merge final
    df_final = df_ads.merge(
        vendas_por_anuncio,
        left_on="codigo_do_anuncio",
        right_on="anuncio_id",
        how="left"
    )    

    df_final = df_final.fillna(0)
    return df_final

def carregar_ads_json(ads_path: str) -> pd.DataFrame:
    """
    Carrega um arquivo JSON de publicidade e retorna como DataFrame.
    """
    if not os.path.exists(ads_path):
        raise FileNotFoundError(f"Arquivo de publicidade não encontrado: {ads_path}")

    with open(ads_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Garante que é uma lista de registros
    if isinstance(data, dict):
        data = [data]

    df_ads = pd.DataFrame(data)
    return df_ads