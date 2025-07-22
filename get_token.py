from ml_client import get_auth_url, exchange_code_for_token

def gerar_token(store: str):
    print(f"\n=== Gerando token para {store} ===")
    url = get_auth_url(store)
    print(f"Acesse esta URL e autorize o app:\n{url}")
    code = input("Cole aqui o code retornado na URL: ").strip()
    token_data = exchange_code_for_token(store, code)
    print(f"✅ Token salvo em tokens/{store}.json")

if __name__ == "__main__":
    conta = input("Digite qual conta deseja gerar o token (MG ou SP): ").strip().upper()
    if conta not in ["MG", "SP"]:
        print("Conta inválida. Use 'MG' ou 'SP'.")
    else:
        gerar_token(conta)
