import json
import sys
from pathlib import Path
from ml_client import save_orders

CONFIG_PATH = Path("config.json")

def main(store=None):
    cfg = json.load(open(CONFIG_PATH, encoding="utf-8"))

    # Se store não for passado, atualiza tudo
    if store is None:
        stores = ["MG", "SP"]
    else:
        stores = [store]

    for loja in stores:
        seller_id = cfg[loja]["seller_id"]
        output_path = cfg[loja]["json_path"]
        print(f"\nBuscando pedidos da conta {loja} (seller_id={seller_id})...")

        save_orders(loja, seller_id, output_path)

if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else None
    main(arg)
