from ml_client import save_orders_incremental, load_config

def main():
    for loja in ["MG", "SP"]:
        cfg = load_config(loja)
        seller_id = cfg["seller_id"]
        output_path = cfg["json_path"]

        print(f"[INFO] Atualizando pedidos de {loja} (incremental)...")
        novos = save_orders_incremental(loja, seller_id, output_path)
        if novos == 0:
            print(f"[INFO] Nenhum novo pedido encontrado para {loja}.")
        else:
            print(f"[INFO] {novos} novos pedidos adicionados ao {loja}.")

if __name__ == "__main__":
    main()
