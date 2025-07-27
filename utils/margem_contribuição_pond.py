import pandas as pd
from rapidfuzz import fuzz, process
from utils.utils_dashboard import carregar_json_para_df

def calcular_margem_ponderada(df_precos, json_path, dias=30, cd=None, min_similarity=60):
    """
    Calcula a Margem de Contribuição Ponderada com base nas vendas dos últimos `dias`,
    usando fuzzy matching. Exibe todos os produtos que não encontraram correspondência.
    """
    try:
        print(f"[DEBUG] Iniciando cálculo Margem Ponderada para {cd or 'TODOS'}...")

        # Filtrar produtos pelo CD, se informado
        if cd and "CD Mercado Livre" in df_precos.columns:
            df_precos = df_precos[df_precos["CD Mercado Livre"] == cd].copy()
            print(f"[DEBUG] Produtos filtrados ({cd}): {len(df_precos)}")

        # Carregar vendas
        df_sales = carregar_json_para_df(json_path)
        if df_sales.empty:
            print("[DEBUG] DataFrame de vendas vazio!")
            return 0.0

        if not all(col in df_sales.columns for col in ["Data da venda", "Valor total", "Produto"]):
            raise KeyError("Colunas 'Produto', 'Data da venda' e 'Valor total' são necessárias no JSON.")

        # Filtrar últimas vendas
        df_sales["Data da venda"] = pd.to_datetime(df_sales["Data da venda"], errors="coerce")
        cutoff = pd.Timestamp.now() - pd.Timedelta(days=dias)
        df_sales_30 = df_sales[df_sales["Data da venda"] >= cutoff].copy()
        df_sales_30["Valor total"] = pd.to_numeric(df_sales_30["Valor total"], errors="coerce")

        sales_by_title = df_sales_30.groupby("Produto")["Valor total"].sum().to_dict()
        total_sales = sum(sales_by_title.values())
        if total_sales == 0:
            print(f"[DEBUG] Nenhuma venda encontrada para {cd or 'TODOS'}.")
            return 0.0

        # Matching por título
        weighted_sum = 0.0
        no_match = []  # Lista de produtos sem match

        for _, row in df_precos.iterrows():
            produto_precos = row.get("Produto", "")
            margin = row.get("% Margem de contribuição", 0.0)
            match = process.extractOne(produto_precos, sales_by_title.keys(), scorer=fuzz.token_sort_ratio)

            if match and match[1] >= min_similarity:
                matched_title = match[0]
                sales_val = sales_by_title[matched_title]
                weight = sales_val / total_sales
                weighted_sum += margin * weight
                print(f"[MATCH-{cd}] '{produto_precos}' ~ '{matched_title}' (sim={match[1]}%) -> vendas={sales_val}")
            else:
                no_match.append(produto_precos)

        # Exibir todos os produtos sem match
        if no_match:
            print("\n[NO MATCH - PRODUTOS SEM CORRESPONDÊNCIA]")
            for p in no_match:
                print(f" - {p}")

        print(f"[DEBUG] Margem Ponderada Final ({cd or 'TODOS'}):", weighted_sum)
        return weighted_sum
    except Exception as e:
        print(f"[ERRO] calcular_margem_ponderada: {e}")
        return 0.0
