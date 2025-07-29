# scripts/update_once.py

import os
import sys
import json
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

# ---------------- CONFIGURAÇÕES INICIAIS ----------------
BASE_PATH = Path(__file__).parent.parent
load_dotenv(BASE_PATH / ".env")

# Fix encoding para Windows
if sys.platform == "win32":
    try:
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer)
    except Exception:
        pass

# Ajusta PATH para encontrar ml_client.py
BASE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if BASE_PATH not in sys.path:
    sys.path.insert(0, BASE_PATH)

from ml_client import load_config, save_orders_incremental

# ---------------- FUNÇÕES AUXILIARES ----------------
def to_utc_z(dt_str):
    """Converte uma data qualquer para UTC e adiciona 'Z' no final."""
    try:
        dt = pd.to_datetime(dt_str, utc=True)
        return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    except Exception:
        return dt_str

def get_last_date(json_path):
    """Retorna a última data encontrada no arquivo JSON em UTC."""
    try:
        if not os.path.exists(json_path):
            return None
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not data:
            return None
        dates = [d.get("date_created") for d in data if "date_created" in d]
        if not dates:
            return None
        last_date = max(dates)
        return to_utc_z(last_date)
    except Exception as e:
        print(f"[WARN] Erro ao obter última data de {json_path}: {e}")
        return None

# ---------------- ATUALIZAÇÃO INCREMENTAL ----------------
def update_once():
    """
    Atualiza apenas as vendas NOVAS para MG e SP,
    usando como referência a última data no backup.
    """
    for loja in ["MG", "SP"]:
        cfg = load_config(loja)
        json_path = cfg["json_path"]

        # Determina a data inicial
        last_date = get_last_date(json_path)
        if last_date:
            start_date = to_utc_z(pd.to_datetime(last_date) + timedelta(seconds=1))
            print(f"[INFO] Última venda registrada em {loja}: {last_date}")
            print(f"[INFO] Buscando vendas de {loja} a partir de {start_date}")
        else:
            start_date = to_utc_z(datetime.now(timezone.utc) - timedelta(days=30))
            print(f"[INFO] Sem histórico de {loja}, buscando últimos 30 dias.")

        end_date = to_utc_z(datetime.now(timezone.utc))

        # Faz a busca incremental
        try:
            novos = save_orders_incremental(
                loja,
                int(cfg["seller_id"]),
                cfg["json_path"],
                start_date=start_date,
                end_date=end_date
            )
            if novos:
                print(f"[INFO] {novos} novos pedidos adicionados para {loja}.")
            else:
                print(f"[INFO] Nenhum novo pedido para {loja}.")
        except Exception as e:
            print(f"[ERROR] Falha ao atualizar {loja}: {e}")
            sys.exit(1)

if __name__ == "__main__":
    update_once()
    print("[SUCCESS] Atualização incremental concluída.")
