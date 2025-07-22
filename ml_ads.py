import requests
from ml_client import get_valid_token, load_config

API_VERSION = "1"

# ========== FUNÇÕES PRINCIPAIS ==========

def listar_anuncios(store: str):
    """
    Lista todos os anúncios ativos da conta (store: MG ou SP).
    """
    cfg = load_config(store)
    token = get_valid_token(store)
    seller_id = cfg["seller_id"]

    url = f"https://api.mercadolibre.com/users/{seller_id}/items/search?status=active"
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()

    results = resp.json().get("results", [])
    return results


def encontrar_advertiser(store: str):
    """
    Faz um loop entre todos os anúncios ativos e tenta encontrar um advertiser_id válido.
    """
    anuncios = listar_anuncios(store)
    if not anuncios:
        print(f"[INFO] Nenhum anúncio ativo encontrado para {store}.")
        return None

    print(f"[INFO] {len(anuncios)} anúncios ativos encontrados para {store}. Tentando localizar advertiser...")
    token = get_valid_token(store)

    for product_id in anuncios:
        url = f"https://api.mercadolibre.com/advertising/advertisers?product_id={product_id}"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Api-Version": API_VERSION
        }
        resp = requests.get(url, headers=headers)
        if resp.status_code == 200:
            advertisers = resp.json().get("advertisers", [])
            if advertisers:
                print(f"[OK] Advertiser encontrado para {product_id}: {advertisers[0]['id']}")
                return advertisers[0]['id']
        else:
            print(f"[X] {product_id} não possui Ads ({resp.status_code})")

    print(f"[ERRO] Nenhum advertiser encontrado para {store}.")
    return None


def listar_campanhas(store: str, advertiser_id: str):
    """
    Lista todas as campanhas vinculadas a um advertiser_id.
    """
    token = get_valid_token(store)
    url = f"https://api.mercadolibre.com/advertising/campaigns?advertiser_id={advertiser_id}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Api-Version": API_VERSION
    }
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    return resp.json()


def relatorio_campanha(store: str, campaign_id: str, date_from: str, date_to: str):
    """
    Obtém relatório de métricas (impressões, cliques, custo, ROAS) para uma campanha.
    """
    token = get_valid_token(store)
    url = f"https://api.mercadolibre.com/advertising/campaigns/{campaign_id}/reports"
    params = {
        "date_from": date_from,
        "date_to": date_to,
        "metrics": "impressions,clicks,cost,conversions,roas"
    }
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Api-Version": API_VERSION
    }
    resp = requests.get(url, headers=headers, params=params)
    resp.raise_for_status()
    return resp.json()


def exibir_resumo_ads(store: str, date_from="2025-07-01", date_to="2025-07-20"):
    """
    Busca advertiser_id automaticamente e exibe resumo das campanhas da conta.
    """
    print(f"\n[INFO] Verificando campanhas de {store}...")
    advertiser_id = encontrar_advertiser(store)
    if not advertiser_id:
        print(f"[ERRO] Nenhum advertiser_id encontrado para {store}.")
        return

    campanhas = listar_campanhas(store, advertiser_id)
    if not campanhas.get("campaigns"):
        print(f"[INFO] Nenhuma campanha ativa para {store}.")
        return

    for camp in campanhas.get("campaigns", []):
        camp_id = camp.get("id")
        camp_name = camp.get("name")
        print(f"\n=== Campanha: {camp_name} (ID: {camp_id}) ===")
        rel = relatorio_campanha(store, camp_id, date_from, date_to)
        print(f" - Impressões: {rel.get('impressions', 0)}")
        print(f" - Cliques: {rel.get('clicks', 0)}")
        print(f" - Custo: R$ {rel.get('cost', 0)/100:.2f}")  # API retorna centavos
        print(f" - Conversões: {rel.get('conversions', 0)}")
        print(f" - ROAS: {rel.get('roas', 0)}")


# ========== EXECUÇÃO ==========
if __name__ == "__main__":
    exibir_resumo_ads("MG")
    exibir_resumo_ads("SP")
