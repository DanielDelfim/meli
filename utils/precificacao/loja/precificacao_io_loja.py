import json
from utils.precificacao import calcular_preco_venda

# Caminho do arquivo JSON
JSON_PATH = r"C:\Users\dmdel\OneDrive\Aplicativos\tokens\precificacao_loja.json"


def carregar_dados():
    """Carrega os dados do produto a partir do arquivo JSON."""
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def salvar_dados(data):
    """Salva os dados atualizados (com preço de venda) no arquivo JSON."""
    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def atualizar_precos():
    """Calcula e atualiza o preço de venda dos produtos no JSON."""
    dados = carregar_dados()

    # Caso o JSON seja uma lista de produtos
    if isinstance(dados, list):
        for produto in dados:
            preco = calcular_preco_venda(produto)
            produto["Preço de Venda"] = preco

    # Caso o JSON seja apenas um único produto (dict)
    elif isinstance(dados, dict):
        preco = calcular_preco_venda(dados)
        dados["Preço de Venda"] = preco

    salvar_dados(dados)
    print("Preços de venda atualizados com sucesso!")


if __name__ == "__main__":
    atualizar_precos()
