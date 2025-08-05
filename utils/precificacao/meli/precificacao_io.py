import pandas as pd
from pathlib import Path

CAMINHO_JSON = Path(r"C:/Users/dmdel/OneDrive/Aplicativos/tokens/precificacao/precificacao_meli.json")

def carregar_dados() -> pd.DataFrame:
    try:
        df = pd.read_json(CAMINHO_JSON)
    except Exception as e:
        raise RuntimeError(f"Erro ao carregar JSON: {e}")
    return df

def salvar_dados(df: pd.DataFrame):
    try:
        df.to_json(CAMINHO_JSON, orient="records", force_ascii=False, indent=2)
    except Exception as e:
        raise RuntimeError(f"Erro ao salvar JSON: {e}")

def atualizar_linha(df: pd.DataFrame, produto_id: int, novos_dados: dict) -> pd.DataFrame:
    if produto_id in df["ID"].values:
        for coluna, valor in novos_dados.items():
            df.loc[df["ID"] == produto_id, coluna] = valor
    return df

def deletar_produto(df: pd.DataFrame, produto_id: int) -> pd.DataFrame:
    return df[df["ID"] != produto_id].reset_index(drop=True)

def adicionar_produto(df: pd.DataFrame, dados_produto: dict) -> pd.DataFrame:
    return pd.concat([df, pd.DataFrame([dados_produto])], ignore_index=True)
