import requests
from ml_client import get_valid_token

def listar_product_ads(store: str):
    token = get_valid_token(store)
    url = "https://api.mercadolibre.com/product_ads/campaigns"
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(url, headers=headers)
    print(f"{store} - Status Code:", resp.status_code)
    print(resp.json())

if __name__ == "__main__":
    listar_product_ads("MG")
    listar_product_ads("SP")
