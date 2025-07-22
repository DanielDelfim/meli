import requests
import json
import pandas as pd
import os
from datetime import datetime

# === 1. Carregar o token ===
TOKEN_PATH = "token.json"

if not os.path.exists(TOKEN_PATH):
    raise FileNotFoundError("❌ Arquivo token.json não encontrado!")

with open(TOKEN_PATH, "r", encoding="utf-8") as f:
    token_data = json.load(f)

ACCESS_TOKEN = token_data.get("access_token")
if not ACCESS_TOKEN:
    raise ValueError("❌ access_token não encontrado no token.json.")

headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}

# === 2. Obter o USER_ID ===
print("🔄 Buscando USER_ID...")
res_user = requests.get("https://api.mercadolibre.com/users/me", headers=headers)

if res_user.status_code != 200:
    raise Exception(f"❌ Erro ao buscar USER_ID: {res_user.status_code} - {res_user.text}")

USER_ID = res_user.json().get("id")
print(f"✅ USER_ID encontrado: {USER_ID}")

# === 3. Buscar TODAS as vendas ===
print("🔄 Buscando todas as vendas históricas...")
offset = 0
limit = 50
dados_vendas = []
total_coletadas = 0

while True:
    url = f"https://api.mercadolibre.com/orders/search?seller={USER_ID}&offset={offset}&limit={limit}&sort=date_asc"
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        print(f"❌ Erro ao buscar vendas: {response.status_code} - {response.text}")
        break

    data = response.json()
    results = data.get("results", [])

    if not results:
        break

    for order in results:
        order_items = order.get("order_items", [])
        if order_items:
            item = order_items[0]
            dados_vendas.append({
                "N.º de venda": order.get("id"),
                "Data da venda": order.get("date_created", "")[:10],
                "Produto": item["item"]["title"],
                "Quantidade": item.get("quantity", 0),
                "Preço unitário": item.get("unit_price", 0),
                "Taxa de venda": item.get("sale_fee", 0),
                "Valor total": order.get("total_amount", 0),
                "Comprador": order.get("buyer", {}).get("nickname", "")
            })
        else:
            dados_vendas.append({
                "N.º de venda": order.get("id"),
                "Data da venda": order.get("date_created", "")[:10],
                "Produto": "",
                "Quantidade": 0,
                "Preço unitário": 0,
                "Taxa de venda": 0,
                "Valor total": order.get("total_amount", 0),
                "Comprador": order.get("buyer", {}).get("nickname", "")
            })

        total_coletadas += 1

    offset += limit
    if total_coletadas % 500 == 0:
        print(f"➡️ {total_coletadas} vendas coletadas até agora...")

print(f"✅ Total de vendas coletadas: {total_coletadas}")

# === 4. Backup em JSON ===
with open("backup_vendas.json", "w", encoding="utf-8") as f:
    json.dump(dados_vendas, f, ensure_ascii=False, indent=4)
print("💾 Backup salvo: backup_vendas.json")

# === 5. Exportar para CSV e Excel ===
df = pd.DataFrame(dados_vendas)

# Ordenar por Data
df["Data da venda"] = pd.to_datetime(df["Data da venda"], errors='coerce')
df = df.sort_values(by="Data da venda")

csv_name = "vendas_api.csv"
df.to_csv(csv_name, index=False, encoding="utf-8-sig")
print(f"💾 Arquivo {csv_name} gerado com sucesso!")

try:
    excel_name = "vendas_api.xlsx"
    df.to_excel(excel_name, index=False)
    print(f"💾 Arquivo {excel_name} gerado com sucesso!")
except Exception as e:
    print(f"⚠ Erro ao salvar Excel: {e}")
