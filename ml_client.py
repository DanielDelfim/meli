import requests
import json
import time
from pathlib import Path
from datetime import datetime

CONFIG_PATH = Path("config.json")
TOKEN_DIR = Path("tokens")
TOKEN_DIR.mkdir(exist_ok=True)

LAST_UPDATE_FILE = Path("tokens/last_update.json")

def load_config(store: str):
    cfg = json.load(open(CONFIG_PATH, encoding="utf-8"))
    return cfg[store]

def get_valid_token(store: str):
    path = TOKEN_DIR / f"{store}.json"
    if not path.exists():
        raise FileNotFoundError(f"Token não encontrado para {store}. Execute a autorização primeiro.")
    token = json.load(open(path, encoding="utf-8"))
    expires_in = token["expires_in"]
    obtained = token["_obtained_at"]
    if time.time() > obtained + expires_in - 60:
        token = refresh_token(store)
    return token["access_token"]

def refresh_token(store: str):
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

def fetch_orders_incremental(store: str, seller_id: int, status="paid"):
    token = get_valid_token(store)
    headers = {"Authorization": f"Bearer {token}"}
    base_url = "https://api.mercadolibre.com/orders/search"

    # Lê última atualização
    last_update = None
    if LAST_UPDATE_FILE.exists():
        data = json.load(open(LAST_UPDATE_FILE, encoding="utf-8"))
        last_update = data.get(store)

    params = {
        "seller": seller_id,
        "status": status,
        "limit": 50,
        "offset": 0,
    }
    if last_update:
        params["order.date_created.from"] = last_update

    all_orders = []
    while True:
        resp = requests.get(base_url, headers=headers, params=params)
        resp.raise_for_status()
        data = resp.json()
        results = data.get("results", [])
        if not results:
            break
        all_orders.extend(results)
        params["offset"] += 50
    return all_orders

def save_orders_incremental(store: str, seller_id: int, path: str) -> int:
    """Adiciona apenas novos pedidos ao JSON existente e retorna a quantidade de pedidos novos"""
    novos_pedidos = fetch_orders_incremental(store, seller_id)
    if not novos_pedidos:
        return 0

    # Lê o arquivo existente
    try:
        with open(path, "r", encoding="utf-8") as f:
            pedidos_existentes = json.load(f)
    except FileNotFoundError:
        pedidos_existentes = []

    # Adiciona apenas pedidos novos
    ids_existentes = {p["id"] for p in pedidos_existentes}
    pedidos_filtrados = [p for p in novos_pedidos if p["id"] not in ids_existentes]

    pedidos_atualizados = pedidos_existentes + pedidos_filtrados

    # Salva o arquivo atualizado
    with open(path, "w", encoding="utf-8") as f:
        json.dump(pedidos_atualizados, f, ensure_ascii=False, indent=2)

    # Atualiza data/hora da última atualização
    agora = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    if LAST_UPDATE_FILE.exists():
        data = json.load(open(LAST_UPDATE_FILE, encoding="utf-8"))
    else:
        data = {}
    data[store] = agora
    with open(LAST_UPDATE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return len(pedidos_filtrados)
