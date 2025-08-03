import sys
from pathlib import Path
from datetime import date, datetime, timedelta

# Adiciona a raiz do projeto ao sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

from utils.utils_filtros import filtrar_vendas_json_por_periodo

# Caminho completo para o JSON
CAMINHO_JSON = BASE_DIR / "tokens" / "vendas" / "backup_vendas_sp_pp.json"

# Mês/ano que você quer testar
ANO = 2025
MES = 8

# Datas de início e fim do mês
data_inicio = date(ANO, MES, 1)
if MES == 12:
    data_fim = (datetime(ANO + 1, 1, 1) - timedelta(days=1)).date()
else:
    data_fim = (datetime(ANO, MES + 1, 1) - timedelta(days=1)).date()

print(f"🔍 Verificando período: {data_inicio} → {data_fim}\n")

# Aplica filtro
df_filtrado = filtrar_vendas_json_por_periodo(str(CAMINHO_JSON), data_inicio, data_fim, unidade="SP")

# Resultados
print(f"✅ Linhas encontradas: {len(df_filtrado)}")

valor_total = df_filtrado["Valor total"].sum()
print(f"💰 Valor total das vendas: R$ {valor_total:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

if not df_filtrado.empty:
    print("\n📄 Primeiras 5 linhas:")
    print(df_filtrado[["Data da venda", "Produto", "Quantidade", "Valor total"]].head())
else:
    print("⚠️ Nenhuma venda encontrada no período.")
