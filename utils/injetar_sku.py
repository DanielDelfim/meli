import json
import os
import unicodedata
from datetime import datetime, date
from rapidfuzz import process, fuzz

# Configuração de paths
BASE_PATH = os.getenv("BASE_PATH", r"C:/Users/dmdel/OneDrive/Aplicativos")
DESIGNER_PATH = os.path.join(BASE_PATH, "Designer")
CUSTOS_PATH = os.path.join(DESIGNER_PATH, "custos.json")
SP_JSON = os.path.join(DESIGNER_PATH, "backup_vendas_sp.json")
MG_JSON = os.path.join(DESIGNER_PATH, "backup_vendas_mg.json")
PREC_PATH = os.path.join(BASE_PATH, "tokens", "precificacao_meli.json")

# Utilitário para normalizar texto

def normalize_str(s: str) -> str:
    if not s:
        return ""
    s = unicodedata.normalize('NFD', s)
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
    s = s.lower()
    s = ''.join(c for c in s if c.isalnum() or c.isspace())
    return ' '.join(s.split())

# Carrega períodos de publicidade do custos.json
with open(CUSTOS_PATH, 'r', encoding='utf-8') as f:
    custos = json.load(f)
mes = custos[0].get('mes_competencia')
periods = {}
for rec in custos:
    if rec.get('mes_competencia') == mes:
        pub = rec.get('publicidade', {}) or {}
        try:
            periods['Araçariguama'] = (
                datetime.fromisoformat(pub.get('data_abertura_sp')).date(),
                datetime.fromisoformat(pub.get('data_fechamento_sp')).date()
            )
        except:
            pass
        try:
            periods['Betim'] = (
                datetime.fromisoformat(pub.get('data_abertura_mg')).date(),
                datetime.fromisoformat(pub.get('data_fechamento_mg')).date()
            )
        except:
            pass
        break
# Validação
for city in ['Araçariguama', 'Betim']:
    if city not in periods:
        raise ValueError(f"Período de anúncio para {city} não encontrado em custos.json")

# Carrega JSON de precificação
with open(PREC_PATH, 'r', encoding='utf-8') as f:
    prec_list = json.load(f)

# Threshold de similaridade
threshold = 60

# Função para construir sales_map e injetar SKU para uma cidade

def process_city(city_name, sales_json_path):
    date_open, date_close = periods[city_name]
    # Monta sales_map
    sales_map = {}
    with open(sales_json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    orders = data if isinstance(data, list) else data.get('orders', [])
    for order in orders:
        try:
            dt = datetime.fromisoformat(order.get('date_created').replace('Z', '+00:00')).date()
        except:
            continue
        if dt < date_open or dt > date_close:
            continue
        items = order.get('order_items') or []
        if not items:
            continue
        info = items[0].get('item', {})
        title = info.get('title', '').strip()
        sku = info.get('seller_custom_field') or info.get('seller_sku')
        if title and sku:
            sales_map[normalize_str(title)] = sku
    # Injeção e relatório
    unmatched = []
    for rec in prec_list:
        if rec.get('CD Mercado Livre') != city_name:
            continue
        prod = rec.get('Produto', '')
        norm_prod = normalize_str(prod)
        # exato
        if norm_prod in sales_map:
            rec['SKU'] = sales_map[norm_prod]
        else:
            match = process.extractOne(norm_prod, list(sales_map.keys()), scorer=fuzz.token_sort_ratio)
            if match and match[1] >= threshold:
                rec['SKU'] = sales_map[match[0]]
            else:
                rec['SKU'] = None
                unmatched.append(prod)
    print(f"City: {city_name} — unmatched items: {len(unmatched)}")
    for item in unmatched:
        print(f" - {item}")

# Processa ambas as cidades
process_city('Araçariguama', SP_JSON)
process_city('Betim', MG_JSON)

# Salva JSON atualizado
with open(PREC_PATH, 'w', encoding='utf-8') as f:
    json.dump(prec_list, f, ensure_ascii=False, indent=2)

print("Injeção completa para ambas as cidades.")