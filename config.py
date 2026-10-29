from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# Coloque o Excel na mesma pasta do projeto ou altere este nome.
EXCEL_NAME = "web skraping meli - Copia.xlsx"
EXCEL_PATH = BASE_DIR / EXCEL_NAME

# Se o arquivo for .xlsm, basta trocar EXCEL_NAME para o nome do .xlsm.
TIMEOUT_MS = 180_000
PAUSA_ENTRE_CONSULTAS = 1.0

# 0 = todos os anúncios encontrados nas páginas configuradas.
# O site pode limitar a quantidade efetivamente disponível.
QTD_RESULTADOS = 0

# Número máximo de páginas por código.
MAX_PAGINAS = 10

# Altura da linha que receberá a imagem.
ALTURA_IMAGEM = 90

# Navegador usado pelo Playwright.
HEADLESS = True
