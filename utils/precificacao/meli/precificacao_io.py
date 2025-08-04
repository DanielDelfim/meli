import json
import pandas as pd
from pathlib import Path

# Caminho para o arquivo de precificação
PRECIFICACAO_JSON = Path("C:/Users/dmdel/OneDrive/Aplicativos/tokens/precificacao_meli.json")


def carregar_dados() -> pd.DataFrame:
    """Carrega os dados de precificação do JSON."""
    if not PRECIFICACAO_JSON.exists():
        return pd.DataFrame()

    try:
        with open(PRECIFICACAO_JSON, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError:
        return pd.DataFrame()

    return pd.DataFrame(data)

def salvar_dados(df: pd.DataFrame) -> bool:
    """Salva o DataFrame atualizado no JSON, convertendo NaN para null e Timestamps para string."""
    df_clean = df.where(pd.notnull(df), None)

    # Converte colunas com Timestamp para string
    for col in df_clean.columns:
        if pd.api.types.is_datetime64_any_dtype(df_clean[col]):
            df_clean[col] = df_clean[col].astype(str)
        else:
            # Verifica valores individuais que ainda podem ser Timestamp
            df_clean[col] = df_clean[col].apply(lambda x: str(x) if isinstance(x, pd.Timestamp) else x)

    try:
        with open(PRECIFICACAO_JSON, "w", encoding="utf-8") as f:
            json.dump(df_clean.to_dict(orient="records"), f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"[ERRO] Falha ao salvar JSON: {e}")
        return False


def salvar_alteracoes_json(id_produto: int, edits: dict) -> bool:
    """Atualiza um produto específico pelo ID."""
    df = carregar_dados()
    if df.empty or "ID" not in df.columns:
        return False

    if id_produto not in df["ID"].values:
        return False

    for key, value in edits.items():
        df.loc[df["ID"] == id_produto, key] = value

    return salvar_dados(df)

def deletar_produto(id_produto: int) -> bool:
    """Deleta um produto pelo ID."""
    df = carregar_dados()
    if df.empty or "ID" not in df.columns:
        return False

    df = df[df["ID"] != id_produto]
    return salvar_dados(df)

def adicionar_produto(produto: dict) -> bool:
    """Adiciona um novo produto ao JSON."""
    df = carregar_dados()

    if df.empty:
        df = pd.DataFrame([produto])
    else:
        if "ID" not in produto:
            max_id = df["ID"].max() if not df["ID"].empty else 0
            produto["ID"] = max_id + 1
        df = pd.concat([df, pd.DataFrame([produto])], ignore_index=True)

    return salvar_dados(df)
