import json
import os
import pandas as pd
from utils.precificacao_calc import calcular_margens

JSON_PATH = "C:/Users/dmdel/OneDrive/Aplicativos/tokens/precificacao_meli.json"

def carregar_dados():
    """Carrega dados do JSON, adiciona IDs se necessário e recalcula lucro/margem."""
    if not os.path.exists(JSON_PATH):
        return pd.DataFrame()

    with open(JSON_PATH, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            return pd.DataFrame()

    if not isinstance(data, list) or len(data) == 0:
        return pd.DataFrame()

    # Adiciona ID sequencial se não existir e recalcula margens
    for idx, item in enumerate(data, start=1):
        if "ID" not in item:
            item["ID"] = idx

        # Se "ID do anúncio" não existir, deixa vazio (para compatibilidade)
        if "ID do anúncio" not in item:
            item["ID do anúncio"] = ""

        # Recalcula Lucro e Margem
        frete_cd, imposto, custo_total, lucro_real, margem_real_pct = calcular_margens(item)
        item["Lucro/Prejuízo Real (R$)"] = round(lucro_real, 2)
        item["% Margem de contribuição"] = round(margem_real_pct / 100, 4)  # Salva decimal ex: 0.12

    # Salva JSON atualizado (IDs e margens)
    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return pd.DataFrame(data)

def salvar_alteracoes_json(id_sel, edits):
    """Salva alterações para um produto no JSON."""
    if not os.path.exists(JSON_PATH):
        return False

    with open(JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    encontrado = False
    for item in data:
        if item.get("ID") == id_sel:
            encontrado = True

            # Validação: ID do anúncio é obrigatório
            if "ID do anúncio" in edits and not edits["ID do anúncio"]:
                return False

            for k, v in edits.items():
                if k in item:
                    item[k] = v
            break

    if encontrado:
        with open(JSON_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    return encontrado

def deletar_produto(id_sel):
    """Remove um produto específico do JSON."""
    if not os.path.exists(JSON_PATH):
        return False

    with open(JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    data = [item for item in data if item.get("ID") != id_sel]

    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return True

def adicionar_produto(novo_item):
    """Adiciona um novo produto ao JSON (ID do anúncio é obrigatório)."""
    if not novo_item.get("ID do anúncio"):
        raise ValueError("⚠️ 'ID do anúncio' é obrigatório para adicionar um novo produto.")

    data = []

    # Carrega dados existentes
    if os.path.exists(JSON_PATH):
        with open(JSON_PATH, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = []

    # Gera novo ID sequencial
    novo_id = max([item.get("ID", 0) for item in data], default=0) + 1
    novo_item["ID"] = novo_id

    # Preenche campos que possam estar ausentes
    campos_padrao = [
        "Produto", "ID do anúncio", "Preço de Compra (R$)", "Preço de Venda Atual (R$)",
        "Rótulo", "Embalagem (R$)", "% Comissão Mercado Livre", "% Marketing do anúncio",
        "Frete Mercado Livre (R$)", "Taxa Fixa Mercado Livre (R$)", "Desconto em Taxas ML (R$)",
        "Lucro/Prejuízo Real (R$)", "% Margem de contribuição"
    ]
    for campo in campos_padrao:
        novo_item.setdefault(campo, 0 if "Preço" in campo or "R$" in campo or "%" in campo else "")

    data.append(novo_item)

    # Salva no JSON
    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return novo_id
