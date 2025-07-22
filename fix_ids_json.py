import json
import os

# Caminho para o JSON
JSON_PATH = "C:/Users/dmdel/OneDrive/Aplicativos/tokens/precificacao_meli.json"

def fix_ids_json():
    if not os.path.exists(JSON_PATH):
        print(f"❌ Arquivo não encontrado: {JSON_PATH}")
        return

    with open(JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Se o arquivo estiver vazio ou não for lista, aborta
    if not isinstance(data, list) or len(data) == 0:
        print("❌ O arquivo JSON está vazio ou em formato incorreto.")
        return

    # Adiciona campo ID se não existir
    modified = False
    for idx, item in enumerate(data, start=1):
        if "ID" not in item:
            item["ID"] = idx
            modified = True

    if modified:
        with open(JSON_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"✅ Campo 'ID' adicionado para {len(data)} produtos no arquivo JSON.")
    else:
        print("ℹ️ Todos os itens já possuem um campo 'ID'. Nenhuma alteração feita.")

if __name__ == "__main__":
    fix_ids_json()
