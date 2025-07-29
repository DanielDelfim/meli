import os
import json
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv
from ml_client import load_config, fetch_orders_incremental

# ---------------- CONFIGURAÇÕES ----------------
BASE_PATH = Path(__file__).parent.parent
load_dotenv(BASE_PATH / ".env")

OUTPUT_DIR = BASE_PATH / "Designer"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Lojas que vamos buscar
LOJAS = ["SP", "MG"]

# Data inicial (pode ser ajustada para o início do histórico)
START_DATE = datetime(2015, 1, 1)

# ---------------- FUNÇÕES AUXILIARES ----------------
def save_json_incremental(path, new_data):
    """Salva novos dados no arquivo JSON sem duplicar registros."""
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                existing = json.load(f)
        except Exception:
            existing = []
    else:
        existing = []

    # Criar um conjunto com IDs já existentes
    existing_ids = {str(e.get("id")) for e in existing}
    filtered_new = [n for n in new_data if str(n.get("id")) not in existing_ids]

    # Se houver dados novos, adiciona e salva
    if filtered_new:
        existing.extend(filtered_new)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(existing, f, ensure_ascii=False, indent=2)
        print(f"  ➕ {len(filtered_new)} novos pedidos adicionados. Total: {len(existing)}")
    else:
        print("  Nenhum pedido novo encontrado.")

def fetch_orders_in_batches(loja, seller_id, output_path):
    """Busca pedidos de uma loja mês a mês e salva no arquivo."""
    today = datetime.utcnow()
    current = START_DATE

    print(f"\n--- Iniciando busca completa para {loja} ---")
    print(f"Período: {START_DATE.date()} → {today.date()}")
    print(f"Arquivo destino: {output_path}")

    while current < today:
        month_start = current
        month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(seconds=1)
        if month_end > today:
            month_end = today

        print(f"\n[{loja}] Buscando período: {month_start.date()} → {month_end.date()}")

        try:
            batch = fetch_orders_incremental(
                loja,
                seller_id,
                start_date=month_start.isoformat(),
                end_date=month_end.isoformat()
            )
            print(f"  {len(batch)} pedidos encontrados.")
            save_json_incremental(output_path, batch)
        except Exception as e:
            print(f"  ⚠️ Erro ao buscar período {month_start.date()} → {month_end.date()}: {e}")

        current = (month_end + timedelta(seconds=1)).replace(hour=0, minute=0, second=0)

# ---------------- EXECUÇÃO PRINCIPAL ----------------
def main():
    for loja in LOJAS:
        cfg = load_config(loja)
        output_file = OUTPUT_DIR / f"{loja}_orders.json"
