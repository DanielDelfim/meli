import time
from dotenv import load_dotenv
from ml_client import load_config, save_orders_incremental

import sys
import time

def atualizar_sp():
    # ... seu código existente ...
    pass

def atualizar_mg():
    # ... seu código existente ...
    pass

def main_loop():
    while True:
        atualizar_sp()
        atualizar_mg()
        time.sleep(3600)

def main_once():
    atualizar_sp()
    atualizar_mg()

if __name__ == "__main__":
    if "--once" in sys.argv:
        main_once()
    else:
        main_loop()

def job():
    """
    Executa a atualização de pedidos para MG e SP.
    """
    for loja in ["MG", "SP"]:
        cfg = load_config(loja)
        print(f"[INFO] Atualizando pedidos de {loja}...")
        try:
            novos = save_orders_incremental(loja, int(cfg["seller_id"]), cfg["json_path"])
            if novos:
                print(f"[INFO] {novos} novos pedidos adicionados para {loja}.")
            else:
                print(f"[INFO] Nenhum novo pedido para {loja}.")
        except Exception as e:
            print(f"[ERROR] Falha ao atualizar {loja}: {e}")


if __name__ == "__main__":
    # Carrega variáveis de ambiente do .env local (Render injeta ENV direto em produção)
    load_dotenv()

    print("[INFO] Iniciando serviço de atualização de pedidos...")
    # Loop infinito, executa job a cada hora
    while True:
        job()
        print("[INFO] Aguardando 1 hora até próxima execução...")
        time.sleep(3600)  # 3600 segundos = 1 hora
