from dotenv import load_dotenv
from ml_client import load_config, save_orders_incremental

def main():
    # carrega .env em dev; em produção o Render injeta as ENV vars
    load_dotenv()

    for loja in ["MG", "SP"]:
        cfg = load_config(loja)
        print(f"[INFO] Atualizando pedidos de {loja}...")
        novos = save_orders_incremental(loja, int(cfg["seller_id"]), cfg["json_path"])
        if novos:
            print(f"[INFO] {novos} novos pedidos adicionados.")
        else:
            print("[INFO] Nenhum novo pedido.")

if __name__ == "__main__":
    main()
