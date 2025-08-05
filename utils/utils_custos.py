import json
from datetime import datetime
from pathlib import Path

CUSTOS_PATH = Path("C:/Users/dmdel/OneDrive/Aplicativos/tokens/custos.json")

def carregar_custos():
    if not CUSTOS_PATH.exists():
        return []
    with open(CUSTOS_PATH, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

def salvar_custos(lista):
    with open(CUSTOS_PATH, "w", encoding="utf-8") as f:
        json.dump(lista, f, indent=2, ensure_ascii=False)

def obter_mes(mes_competencia: str):
    """
    Recebe mes_competencia no formato 'YYYY-MM'
    """
    custos = carregar_custos()
    for c in custos:
        if c.get("mes_competencia") == mes_competencia:
            return c
    return None

def atualizar_custo_mes(mes_competencia: str, novos_valores: dict):
    """
    Atualiza ou cria um mês específico de custo
    """
    custos = carregar_custos()
    nova_lista = []
    encontrado = False

    for c in custos:
        if c.get("mes_competencia") == mes_competencia:
            c.update(novos_valores)
            encontrado = True
        nova_lista.append(c)

    if not encontrado:
        novos_valores["mes_competencia"] = mes_competencia
        nova_lista.append(novos_valores)

    # Ordena pela data no formato novo 'YYYY-MM'
    salvar_custos(sorted(nova_lista, key=lambda x: datetime.strptime(x["mes_competencia"], "%Y-%m")))

def adicionar_novo_custo_a_todos_os_meses(nome: str, valor):
    """
    Adiciona um novo custo com valor fixo em todos os meses
    """
    custos = carregar_custos()
    for c in custos:
        if nome not in c:
            c[nome] = valor
    salvar_custos(custos)

def excluir_mes(mes_competencia: str):
    """
    Remove o mês informado
    """
    custos = carregar_custos()
    nova_lista = [c for c in custos if c.get("mes_competencia") != mes_competencia]
    salvar_custos(nova_lista)
