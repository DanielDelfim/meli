import json
import requests

# --- Carregar token salvo ---
with open("token.json", "r") as f:
    token_data = json.load(f)

ACCESS_TOKEN = token_data.get("access_token")
headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}

# --- Buscar USER_ID ---
url = "https://api.mercadolibre.com/users/me"
response = requests.get(url, headers=headers)

if response.status_code == 200:
    dados = response.json()
    print("Seu USER_ID é:", dados.get("id"))
    print("Nome do usuário:", dados.get("nickname"))
else:
    print("Erro ao buscar USER_ID:", response.status_code, response.text)
