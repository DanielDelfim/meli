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


# ---------------- CONFIGURAÇÕES ----------------
def load_config(loja: str) -> dict:
    prefix = loja.upper()  # "SP" ou "MG"

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


# ---------------- TOKEN ----------------
def get_valid_token(store: str) -> str:
    """
    Retorna um token válido para a loja, fazendo refresh se necessário.
    Se não existir arquivo, tenta carregar de ENV var <STORE>_TOKEN_JSON.
    """
    path = token_dir / f"{store}.json"

    if not path.exists():
        env_key = f"{store}_TOKEN_JSON"
        raw = os.getenv(env_key)
        if not raw:
            raise FileNotFoundError(
                f"Token não encontrado para {store}. Nem arquivo nem ENV var {env_key}."
            )
        try:
            token = json.loads(raw)
        except json.JSONDecodeError:
            raise ValueError(f"Conteúdo de {env_key} não é JSON válido.")

        if "_obtained_at" not in token:
            token["_obtained_at"] = int(time.time())

        with open(path, "w", encoding="utf-8") as f:
            json.dump(token, f, ensure_ascii=False, indent=2)
    else:
        token = json.load(open(path, encoding="utf-8"))

    if time.time() > token.get("_obtained_at", 0) + token.get("expires_in", 0) - 60:
        token = refresh_token(store)
    return token["access_token"]


def refresh_token(store: str) -> dict:
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


# ---------------- ORDERS ----------------
def fetch_all_orders(store: str, seller_id: int, status="paid") -> list:
    """
    Busca TODAS as vendas de uma loja (paginando até o fim).
    """
    token = get_valid_token(store)
    headers = {"Authorization": f"Bearer {token}"}
    url = "https://api.mercadolibre.com/orders/search"

    params = {
        "seller": seller_id,
        "status": status,
        "limit": 50,
        "offset": 0,
        "sort": "date_asc"  # ordem cronológica
    }

    all_orders = []
    total = 0
    while True:
        resp = requests.get(url, headers=headers, params=params)
        resp.raise_for_status()
        data = resp.json()
        batch = data.get("results", [])
        if not batch:
            break
        all_orders.extend(batch)
        total += len(batch)
        print(f"[INFO] {store}: {total} pedidos coletados...")
        params["offset"] += 50
        if len(batch) < 50:
            break

    return all_orders


def save_all_orders(store: str, seller_id: int, path: str) -> int:
    """
    Busca todas as vendas e salva em um único JSON (sobrescrevendo o arquivo).
    """
    todos = fetch_all_orders(store, seller_id)
    if not todos:
        print(f"[INFO] Nenhum pedido encontrado para {store}.")
        return 0

    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(todos, f, ensure_ascii=False, indent=2)

    print(f"[INFO] {len(todos)} pedidos salvos em {path}")
    return len(todos)


# ---------------- INCREMENTAL (MANTIDO) ----------------
def fetch_orders_incremental(store: str, seller_id: int, start_date=None, end_date=None, status="paid") -> list:
    """
    Busca pedidos no intervalo definido.
    """
    token = get_valid_token(store)
    headers = {"Authorization": f"Bearer {token}"}
    url = "https://api.mercadolibre.com/orders/search"

    params = {
        "seller": seller_id,
        "status": status,
        "limit": 50,
        "offset": 0,
        "sort": "date_desc"
    }

    if start_date and end_date:
        params["order.date_created.from"] = start_date
        params["order.date_created.to"] = end_date

    all_orders = []
    while True:
        resp = requests.get(url, headers=headers, params=params)
        resp.raise_for_status()
        data = resp.json()
        batch = data.get("results", [])
        if not batch:
            break
        all_orders.extend(batch)
        params["offset"] += 50
        if len(batch) < 50:
            break

    return all_orders


def save_orders_incremental(store: str, seller_id: int, path: str, start_date=None, end_date=None) -> int:
    """
    Salva pedidos incrementais no arquivo JSON.
    """
    novos = fetch_orders_incremental(store, seller_id, start_date, end_date)
    if not novos:
        print(f"[INFO] Nenhum pedido novo para {store}.")
        return 0

    try:
        with open(path, "r", encoding="utf-8") as f:
            existentes = json.load(f)
    except FileNotFoundError:
        existentes = []

    ids_existentes = {p["id"] for p in existentes}
    filtrados = [p for p in novos if p["id"] not in ids_existentes]
    atualizados = existentes + filtrados

    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(atualizados, f, ensure_ascii=False, indent=2)

    print(f"[INFO] {len(filtrados)} novos pedidos adicionados para {store}.")
    return len(filtrados)
