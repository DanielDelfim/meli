import requests
import json
import time
from urllib.parse import urlencode
from pathlib import Path

CONFIG_PATH = Path("config.json")
TOKEN_DIR = Path("tokens")
TOKEN_DIR.mkdir(exist_ok=True)

def load_config(store: str):
    cfg = json.load(open(CONFIG_PATH, encoding="utf-8"))
    return cfg[store]

def get_auth_url(store: str):
    """Gera a URL para o usuário autorizar a app e devolver o `code`."""
    cfg = load_config(store)
    params = {
        "response_type": "code",
        "client_id": cfg["client_id"],
        "redirect_uri": cfg["redirect_uri"]
    }
    return "https://auth.mercadolivre.com.br/authorization?" + urlencode(params)

def exchange_code_for_token(store: str, code: str):
    """Troca o code retornado no redirect por access + refresh tokens."""
    cfg = load_config(store)
    data = {
        "grant_type": "authorization_code",
        "client_id": cfg["client_id"],
        "client_secret": cfg["client_secret"],
        "code": code,
        "redirect_uri": cfg["redirect_uri"],
    }
    resp = requests.post("https://api.mercadolibre.com/oauth/token", data=data)
    resp.raise_for_status()
    token_data = resp.json()
    token_data["_obtained_at"] = int(time.time())
    with open(TOKEN_DIR / f"{store}.json", "w", encoding="utf-8") as f:
        json.dump(token_data, f, ensure_ascii=False, indent=2)
    return token_data

def refresh_token(store: str):
    """Renova o access_token usando o refresh_token salvo."""
    cfg = load_config(store)
    token = json.load(open(TOKEN_DIR / f"{store}.json", encoding="utf-8"))
    data = {
        "grant_type": "refresh_token",
        "client_id": cfg["client_id"],
        "client_secret": cfg["client_secret"],
        "refresh_token": token["refresh_token"],
    }
    resp = requests.post("https://api.mercadolibre.com/oauth/token", data=data)
    resp.raise_for_status()
    token_data = resp.json()
    token_data["_obtained_at"] = int(time.time())
    with open(TOKEN_DIR / f"{store}.json", "w", encoding="utf-8") as f:
        json.dump(token_data, f, ensure_ascii=False, indent=2)
    return token_data

def get_valid_token(store: str):
    """Retorna um access_token válido, renovando se necessário."""
    path = TOKEN_DIR / f"{store}.json"
    if not path.exists():
        raise FileNotFoundError(f"Primeiro execute `exchange_code_for_token('{store}', <code>)`")
    token = json.load(open(path, encoding="utf-8"))
    if "_obtained_at" not in token:
        token["_obtained_at"] = 0  # Força renovação se campo não existe
    expires_in = token["expires_in"]
    obtained = token["_obtained_at"]
    if time.time() > obtained + expires_in - 60:
        token = refresh_token(store)
    return token["access_token"]

def fetch_all_orders(store: str, seller_id: int, status: str = "paid"):
    """Busca recursivamente todas as orders do seller."""
    token = get_valid_token(store)
    headers = {"Authorization": f"Bearer {token}"}
    base_url = "https://api.mercadolibre.com/orders/search"
    limit = 50
    offset = 0
    all_orders = []

    while True:
        params = {
            "seller": seller_id,
            "status": status,
            "limit": limit,
            "offset": offset
        }
        resp = requests.get(base_url, headers=headers, params=params)
        resp.raise_for_status()
        data = resp.json()
        results = data.get("results", [])
        if not results:
            break
        all_orders.extend(results)
        offset += limit
    return all_orders

def save_orders(store: str, seller_id: int, path: str):
    """Busca todas as orders e salva num JSON no path indicado."""
    orders = fetch_all_orders(store, seller_id)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(orders, f, ensure_ascii=False, indent=2)
    print(f"{len(orders)} vendas salvas em {path}")

