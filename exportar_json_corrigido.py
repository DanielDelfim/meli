import pandas as pd
import json

EXCEL_PATH = "C:/Users/dmdel/OneDrive/Aplicativos/Planilha_Precificacao_Supramel_MargemLiquida.xlsx"
JSON_PATH = "C:/Users/dmdel/OneDrive/Aplicativos/tokens/precificacao_meli.json"

def exportar_planilha_corrigida():
    print("🔄 Lendo a aba MELI do Excel...")
    df = pd.read_excel(EXCEL_PATH, sheet_name="MELI", skiprows=1)

    # Remove espaços extras nos nomes das colunas
    df.columns = df.columns.str.strip()

    # Lista de colunas de porcentagem para conversão
    colunas_pct = [
        "% Comissão Mercado Livre",
        "% Marketing do anúncio",
        "% Marketing real",
        "% Margem de contribuição",
        "% Margem de contribuição sem Marketing",
        "% Imposto Simples Nacional",
        "% Substituição Tributária"
    ]

    # Converte porcentagens em formato decimal (ex: 14% -> 0.14)
    for col in colunas_pct:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
            # Se os valores já estão em formato decimal, mantém como está.
            # Caso estejam como 14 (em vez de 0.14), dividimos por 100.
            if df[col].max() > 1:
                df[col] = df[col] / 100

    # Converte demais colunas numéricas (com R$ ou valores financeiros)
    colunas_numericas = [
        "Preço de Venda Atual (R$)",
        "Preço de Compra (R$)",
        "Frete até cd (R$)",
        "Rótulo",
        "Embalagem (R$)",
        "Frete Mercado Livre (R$)",
        "Taxa Fixa Mercado Livre (R$)",
        "Desconto em Taxas ML (R$)",
        "Lucro/Prejuízo Real (R$)",
        "Preço com marketing real (R$)",
        "Preço final"
    ]
    for col in colunas_numericas:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    # Preenche células vazias de texto com string vazia
    df = df.fillna("")

    # Exporta para JSON
    print(f"💾 Exportando {len(df)} registros para JSON...")
    df.to_json(JSON_PATH, orient="records", force_ascii=False, indent=2)
    print(f"✅ Arquivo gerado com sucesso: {JSON_PATH}")

if __name__ == "__main__":
    exportar_planilha_corrigida()
