import os
import json
import pandas as pd
from pathlib import Path
from datetime import datetime

# Caminhos base
BASE_PATH = Path(__file__).parent.parent
DESIGNER_PATH = BASE_PATH / "Designer"

# Arquivos de entrada possíveis
INPUT_FILES = {
    "SP": DESIGNER_PATH / "vendas_sp.json",
    "MG": DESIGNER_PATH / "vendas_mg.json"
}

# Arquivos de saída pré-processados
OUTPUT_FILES = {
    "SP": BASE_PATH / "tokens" / "vendas" / "backup_vendas_sp_pp.json",
    "MG": BASE_PATH / "tokens" / "vendas" / "backup_vendas_mg_pp.json"
}

def preprocess_json(input_path, output_path, uf):
    """Pré-processa JSON de vendas incluindo SKU e campos essenciais."""
    if not input_path.exists():
        print(f"⚠️ {uf}: Arquivo não encontrado: {input_path}")
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False, indent=2)
        return

    try:
        with open(input_path, "r", encoding="utf-8") as f:
            vendas = json.load(f)

        if not isinstance(vendas, list):
            print(f"⚠️ {uf}: JSON não está no formato esperado (lista).")
            vendas = []

        registros = []
        for record in vendas:
            dt = record.get("date_created") or record.get("Data da venda")
            dt_parsed = pd.to_datetime(dt, errors="coerce", utc=True)
            if pd.notna(dt_parsed):
                data_venda = dt_parsed.tz_convert("America/Sao_Paulo").date().isoformat()

                order_items = record.get("order_items", [])
                if isinstance(order_items, list) and order_items:
                    for item in order_items:
                        registros.append({
                            "Data da venda": data_venda,
                            "Produto": item.get("item", {}).get("title", "Produto não identificado"),
                            "SKU": item.get("item", {}).get("seller_sku", ""),
                            "Quantidade": item.get("quantity", 0),
                            "Valor total": round(item.get("unit_price", 0) * item.get("quantity", 0), 2),
                            "codigo_do_anuncio": item.get("item", {}).get("id", ""),
                            "Unidade": uf
                        })
                else:
                    registros.append({
                        "Data da venda": data_venda,
                        "Produto": "Produto não identificado",
                        "SKU": "",
                        "Quantidade": 1,
                        "Valor total": record.get("total_amount", 0),
                        "codigo_do_anuncio": "",
                        "Unidade": uf
                    })

        # Salva o arquivo processado
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(registros, f, ensure_ascii=False, indent=2)

        print(f"✅ {uf}: {len(registros)} registros processados e salvos em {output_path}")

        if registros:
            df = pd.DataFrame(registros)
            resumo = df.groupby("Data da venda")["Quantidade"].sum()
            print(f"📊 {uf}: Vendas por dia:\n{resumo}")

    except Exception as e:
        print(f"❌ {uf}: Erro ao processar {input_path}: {e}")
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False, indent=2)

def main():
    print("🔄 Iniciando pré-processamento de vendas...")
    print(f"📂 Pasta de trabalho: {DESIGNER_PATH}")

    DESIGNER_PATH.mkdir(exist_ok=True)

    for uf, input_path in INPUT_FILES.items():
        print(f"\n--- Processando {uf} ---")
        preprocess_json(input_path, OUTPUT_FILES[uf], uf)

    print("\n✅ Pré-processamento concluído!")

if __name__ == "__main__":
    main()
