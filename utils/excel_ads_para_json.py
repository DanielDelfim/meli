import pandas as pd
import unicodedata
import os

# Mapeamento de arquivos Excel para JSON (mantendo também os relatórios de 07d)
FILES_MAPPING = [
    {
        "excel": r"C:\Users\dmdel\OneDrive\Aplicativos\Relatorio_anuncios_patrocinados_07d_total_SP.xlsx",
        "json": r"C:\Users\dmdel\OneDrive\Aplicativos\Designer\ads_sp.json"
    },
    {
        "excel": r"C:\Users\dmdel\OneDrive\Aplicativos\Relatorio_anuncios_patrocinados_07d_total_MG.xlsx",
        "json": r"C:\Users\dmdel\OneDrive\Aplicativos\Designer\ads_mg.json"
    },
    {
        "excel": r"C:\Users\dmdel\OneDrive\Aplicativos\Relatorio_anuncios_patrocinados_15d_total_MG.xlsx",
        "json": r"C:\Users\dmdel\OneDrive\Aplicativos\Designer\ads_15d_mg.json"
    },
    {
        "excel": r"C:\Users\dmdel\OneDrive\Aplicativos\Relatorio_anuncios_patrocinados_15d_total_SP.xlsx",
        "json": r"C:\Users\dmdel\OneDrive\Aplicativos\Designer\ads_15d_sp.json"
    },
    {
        "excel": r"C:\Users\dmdel\OneDrive\Aplicativos\Relatorio_anuncios_patrocinados_mes_total_MG.xlsx",
        "json": r"C:\Users\dmdel\OneDrive\Aplicativos\Designer\ads_mes_mg.json"
    },
    {
        "excel": r"C:\Users\dmdel\OneDrive\Aplicativos\Relatorio_anuncios_patrocinados_mes_total_SP.xlsx",
        "json": r"C:\Users\dmdel\OneDrive\Aplicativos\Designer\ads_mes_sp.json"
    },
]


def normalizar_texto(texto: str) -> str:
    """
    Remove acentuação, quebras de linha e normaliza texto para snake_case.
    """
    if not isinstance(texto, str):
        return texto
    texto = texto.strip().replace("\n", "_")
    texto = unicodedata.normalize("NFKD", texto).encode("ASCII", "ignore").decode("ASCII")
    return texto.lower().replace(" ", "_")


def excel_para_json(excel_path: str, json_path: str):
    """
    Lê o Excel, normaliza colunas e salva em JSON.
    """
    df = pd.read_excel(excel_path, skiprows=1)
    df.columns = [normalizar_texto(col) for col in df.columns]
    # Garante diretório de saída
    os.makedirs(os.path.dirname(json_path), exist_ok=True)
    df.to_json(json_path, orient="records", force_ascii=False, indent=2)
    print(f"✅ Convertido: {excel_path} → {json_path}")


if __name__ == "__main__":
    for mapping in FILES_MAPPING:
        excel_para_json(mapping["excel"], mapping["json"])
