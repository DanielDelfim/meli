import json
import requests

# --- 1. Carregar configurações ---
try:
    with open("config.json", "r") as f:
        config = json.load(f)
        CLIENT_ID = config.get("client_id")
        USER_ID = config.get("user_id")  # Pode estar vazio se quiser buscar via API
except FileNotFoundError:
    print("❌ Arquivo config.json não encontrado. Crie o arquivo com CLIENT_ID e USER_ID.")
    exit()

# --- 2. Carregar Access Token ---
try:
    with open("token.json", "r") as f:
        token_data = json.load(f)
        ACCESS_TOKEN = token_data.get("access_token")
except FileNotFoundError:
    print("❌ Arquivo token.json não encontrado. Gere o token primeiro.")
    exit()

if not ACCESS_TOKEN:
    print("❌ Access Token inválido ou vazio.")
    exit()

headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}

# --- 3. Se USER_ID estiver vazio, buscar automaticamente ---
if not USER_ID:
    print("🔄 Buscando USER_ID automaticamente...")
    res_user = requests.get("https://api.mercadolibre.com/users/me", headers=headers)
    if res_user.status_code == 200:
        user_data = res_user.json()
        USER_ID = user_data.get("id")
        print(f"✅ USER_ID encontrado: {USER_ID}")
    else:
        print(f"❌ Erro ao buscar USER_ID: {res_user.status_code} - {res_user.text}")
        exit()

# --- 4. Buscar 1 venda para explorar campos ---
url = f"https://api.mercadolibre.com/orders/search?seller={USER_ID}&order.status=paid&limit=1"
response = requests.get(url, headers=headers)

if response.status_code != 200:
    print(f"❌ Erro ao buscar vendas: {response.status_code} - {response.text}")
    exit()

dados = response.json()
orders = dados.get("results", [])

if not orders:
    print("⚠ Nenhuma venda encontrada.")
    exit()

# --- 5. Mostrar toda a estrutura da primeira venda ---
primeira_venda = orders[0]
print("\n=== Estrutura completa da primeira venda ===\n")
print(json.dumps(primeira_venda, indent=4, ensure_ascii=False))
