import json
import pandas as pd
from pathlib import Path

# Caminho para o arquivo de precificação
BASE_PATH = Path(__file__).resolve().parent.parent
PRECIFICACAO_JSON = BASE_PATH / "tokens" / "precificacao_meli.json"

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

def salvar_dados(df: pd.DataFrame):
    """Salva o DataFrame atualizado no JSON."""
    try:
        with open(PRECIFICACAO_JSON, "w", encoding="utf-8") as f:
            json.dump(df.to_dict(orient="records"), f, ensure_ascii=False, indent=2)
        return True
    except Exception:
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
