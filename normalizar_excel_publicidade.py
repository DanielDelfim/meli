import pandas as pd
import unicodedata
import os

# Caminhos dos arquivos originais
EXCEL_SP = r"C:\Users\dmdel\OneDrive\Aplicativos\Relatorio_anuncios_patrocinados_07d_total_SP.xlsx"
EXCEL_MG = r"C:\Users\dmdel\OneDrive\Aplicativos\Relatorio_anuncios_patrocinados_07d_total_MG.xlsx"

# Caminhos dos arquivos corrigidos
EXCEL_SP_SAIDA = r"C:\Users\dmdel\OneDrive\Aplicativos\Relatorio_anuncios_patrocinados_07d_total_SP_NORMALIZADO.xlsx"
EXCEL_MG_SAIDA = r"C:\Users\dmdel\OneDrive\Aplicativos\Relatorio_anuncios_patrocinados_07d_total_MG_NORMALIZADO.xlsx"


def normalizar_texto(texto: str) -> str:
    """Remove acentos, espaços extras, quebras de linha e converte para minúsculo com underscores."""
    if not isinstance(texto, str):
        return texto
    texto = texto.strip()
    texto = texto.replace("\n", "_")
    texto = unicodedata.normalize("NFKD", texto).encode("ASCII", "ignore").decode("ASCII")
    texto = texto.lower().replace(" ", "_")
    return texto


def normalizar_excel(arquivo_origem: str, arquivo_destino: str):
    if not os.path.exists(arquivo_origem):
        print(f"❌ Arquivo não encontrado: {arquivo_origem}")
        return

    print(f"🔄 Lendo o Excel: {arquivo_origem}")
    df = pd.read_excel(arquivo_origem, skiprows=1)

    # Normalizar colunas
    colunas_originais = df.columns.tolist()
    df.columns = [normalizar_texto(col) for col in df.columns]

    print("📑 Colunas originais:")
    print(colunas_originais)
    print("✅ Colunas normalizadas:")
    print(df.columns.tolist())

    # Salvar arquivo corrigido
    df.to_excel(arquivo_destino, index=False)
    print(f"💾 Arquivo normalizado salvo em: {arquivo_destino}\n")


def main():
    print("=== NORMALIZAÇÃO DAS PLANILHAS DE PUBLICIDADE ===")
    normalizar_excel(EXCEL_SP, EXCEL_SP_SAIDA)
    normalizar_excel(EXCEL_MG, EXCEL_MG_SAIDA)
    print("✅ Processo finalizado com sucesso.")


if __name__ == "__main__":
    main()
