import os
import json
import pandas as pd
from utils.utils_dashboard import carregar_json_para_df  # Reutiliza carregamento de vendas

# Caminhos base para arquivos de publicidade
BASE_PATH = r"C:\Users\dmdel\OneDrive\Aplicativos"
DESIGNER_PATH = os.path.join(BASE_PATH, "Designer")

# Mapeamento de todos os JSONs de anúncios
JSON_ADS_FILES = {
    'ads_sp': os.path.join(DESIGNER_PATH, 'ads_sp.json'),
    'ads_mg': os.path.join(DESIGNER_PATH, 'ads_mg.json'),
    'ads_15d_sp': os.path.join(DESIGNER_PATH, 'ads_15d_sp.json'),
    'ads_15d_mg': os.path.join(DESIGNER_PATH, 'ads_15d_mg.json'),
    'ads_mes_sp': os.path.join(DESIGNER_PATH, 'ads_mes_sp.json'),
    'ads_mes_mg': os.path.join(DESIGNER_PATH, 'ads_mes_mg.json'),
}


def carregar_ads_json(ads_path: str) -> pd.DataFrame:
    """
    Carrega um JSON de anúncios (lista de registros) e retorna um DataFrame.
    """
    if not os.path.exists(ads_path):
        raise FileNotFoundError(f"Arquivo não encontrado: {ads_path}")
    with open(ads_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    if isinstance(data, dict):
        data = [data]
    df = pd.json_normalize(data)
    # Normaliza colunas para snake_case
    df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_').str.replace('__', '_')
    return df


def carregar_ads(file_path: str) -> pd.DataFrame:
    """
    Carrega arquivo de anúncios (CSV, XLSX ou JSON) e retorna um DataFrame.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")
    ext = os.path.splitext(file_path)[1].lower()
    if ext == '.json':
        df = pd.read_json(file_path)
    elif ext in ['.xls', '.xlsx']:
        df = pd.read_excel(file_path, skiprows=1)
    elif ext == '.csv':
        df = pd.read_csv(file_path, skiprows=1)
    else:
        raise ValueError(f"Formato não suportado: {ext}")
    # Normaliza colunas
    df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_').str.replace('__', '_')
    return df


def carregar_todos_ads_json() -> dict:
    """
    Carrega todos os JSONs em JSON_ADS_FILES e retorna dict de DataFrames.
    """
    return {key: carregar_ads_json(path) for key, path in JSON_ADS_FILES.items()}


def preparar_dataframe_publicidade(vendas_json: str, ads_path: str, start_date=None, end_date=None) -> pd.DataFrame:
    """
    Combina dados de publicidade (ads_path) com vendas (vendas_json), aplicando filtro de datas baseado em 'Data da venda'.

    Retorna DataFrame com colunas:
    - vendas_sim, vendas_nao, total_vendas
    - receita_sim, receita_nao, receita_total
    """
    # Carrega dados
    df_ads = carregar_ads_json(ads_path)
    df_vendas = carregar_json_para_df(vendas_json)

    # Filtra pelo período, se informado
    if start_date and end_date:
        # Filtrar apenas pela data (sem horário) para garantir consistência
        df_vendas['dia_venda'] = df_vendas['Data da venda'].dt.date
        df_vendas = df_vendas[
            df_vendas['dia_venda'].between(pd.to_datetime(start_date).date(),
                                           pd.to_datetime(end_date).date())
        ]

    # Extrai ID do anúncio
    df_vendas['anuncio_id'] = df_vendas['order_items'].apply(
        lambda x: x[0]['item']['id'] if isinstance(x, list) and x else None
    )

    # Agrupa para contagem de vendas
    count_df = (
        df_vendas
        .groupby(['anuncio_id', 'via_ads'])
        .size()
        .unstack(fill_value=0)
        .rename(columns={'Sim': 'vendas_sim', 'Não': 'vendas_nao'})
    )

    # Agrupa para soma de receita (usa mesma coluna de receita orgânica)
    rev_df = (
        df_vendas
        .groupby(['anuncio_id', 'via_ads'])['Valor total']
        .sum()
        .unstack(fill_value=0)
        .rename(columns={'Sim': 'receita_sim', 'Não': 'receita_nao'})
    )

    # Combina contagem e receita
    agg = count_df.join(rev_df, how='outer').fillna(0).reset_index()

    # Campos totais
    agg['total_vendas'] = agg['vendas_sim'] + agg['vendas_nao']
    agg['receita_total'] = agg['receita_sim'] + agg['receita_nao']

    # Merge final com dados de anúncios
    df_final = (
        df_ads
        .merge(agg, left_on='codigo_do_anuncio', right_on='anuncio_id', how='left')
        .fillna(0)
    )
    return df_final
