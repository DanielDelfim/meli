import os
import json
import time
import requests
from pathlib import Path
from datetime import datetime

# Diretórios para tokens e último update
token_dir = Path("tokens")
token_dir.mkdir(exist_ok=True)
LAST_UPDATE_FILE = token_dir / "last_update.json"


def load_config(loja: str) -> dict:
    """
    Carrega as configurações de ambiente para a loja (SP ou MG).
    Espera encontrar as variáveis:
      - <LOJA>_JSON_PATH
      - <LOJA>_CLIENT_ID
      - <LOJA>_CLIENT_SECRET
      - <LOJA>_SELLER_ID
      - <LOJA>_REDIRECT_URI
    """
    prefix = loja.upper()

    json_path = os.getenv(f"{prefix}_JSON_PATH")
    if not json_path:
        raise RuntimeError(f"❌ Variável {prefix}_JSON_PATH não definida.")

    return {
        "json_path":     json_path,
        "client_id":     os.getenv(f"{prefix}_CLIENT_ID", ""),
        "client_secret": os.getenv(f"{prefix}_CLIENT_SECRET", ""),
        "seller_id":     os.getenv(f"{prefix}_SELLER_ID", ""),
        "redirect_uri":  os.getenv(f"{prefix}_REDIRECT_URI", ""),
    }


def get_valid_token(store: str) -> str:
    """
    Retorna um token válido para a loja, fazendo refresh se necessário.
    Procura o arquivo tokens/<store>.json e, se não existir, dispara erro.
    """
    path = token_dir / f"{store}.json"
    if not path.exists():
        raise FileNotFoundError(f"Token não encontrado para {store}. Execute a autorização primeiro.")

    token = json.load(open(path, encoding="utf-8"))
    # Se estiver expirando em menos de 60s, atualiza
    if time.time() > token.get("_obtained_at", 0) + token.get("expires_in", 0) - 60:
        token = refresh_token(store)

    return token["access_token"]


def refresh_token(store: str) -> dict:
    """
    Refresha o token de acesso usando o refresh_token.
    """
    cfg = load_config(store)
    token_path = token_dir / f"{store}.json"
    token = json.load(open(token_path, encoding="utf-8"))

    payload = {
        "grant_type":    "refresh_token",
        "client_id":     cfg["client_id"],
        "client_secret": cfg["client_secret"],
        "refresh_token": token["refresh_token"],
    }
    resp = requests.post("https://api.mercadolibre.com/oauth/token", data=payload)
    resp.raise_for_status()

    token_data = resp.json()
    token_data["_obtained_at"] = int(time.time())
    with open(token_path, "w", encoding="utf-8") as f:
        json.dump(token_data, f, ensure_ascii=False, indent=2)

    return token_data


def fetch_orders_incremental(store: str, seller_id: int, status: str = "paid") -> list:
    """
    Busca de forma incremental todos os pedidos com status dado desde a última data salva.
    """
    token = get_valid_token(store)
    headers = {"Authorization": f"Bearer {token}"}
    url = "https://api.mercadolibre.com/orders/search"

    # Carrega última data
    last_update = None
    if LAST_UPDATE_FILE.exists():
        data = json.load(open(LAST_UPDATE_FILE, encoding="utf-8"))
        last_update = data.get(store)

    params = {"seller": seller_id, "status": status, "limit": 50, "offset": 0}
    if last_update:
        params["order.date_created.from"] = last_update

    all_orders = []
    while True:
        resp = requests.get(url, headers=headers, params=params)
        resp.raise_for_status()
        batch = resp.json().get("results", [])
        if not batch:
            break
        all_orders.extend(batch)
        params["offset"] += 50

    return all_orders


def save_orders_incremental(store: str, seller_id: int, path: str) -> int:
    """
    Adiciona apenas pedidos novos ao JSON existente e retorna a quantidade adicionada.
    """
    novos = fetch_orders_incremental(store, seller_id)
    if not novos:
        return 0

    # Lê pedidos existentes
    try:
        with open(path, "r", encoding="utf-8") as f:
            existentes = json.load(f)
    except FileNotFoundError:
        existentes = []

    ids_existentes = {p["id"] for p in existentes}
    filtrados = [p for p in novos if p["id"] not in ids_existentes]
    atualizados = existentes + filtrados

    # Salva em disco
    with open(path, "w", encoding="utf-8") as f:
        json.dump(atualizados, f, ensure_ascii=False, indent=2)

    # Atualiza timestamp
    agora = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    if LAST_UPDATE_FILE.exists():
        data = json.load(open(LAST_UPDATE_FILE, encoding="utf-8"))
    else:
        data = {}
    data[store] = agora
    with open(LAST_UPDATE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return len(filtrados)
