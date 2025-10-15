import os
import sys
from dotenv import load_dotenv

load_dotenv()

APP_NAME = os.getenv("APP_NAME", "Mymoney")

# Diretório base: suporta execução empacotada (PyInstaller) e desenvolvimento
if getattr(sys, 'frozen', False):
    # Executável: usa _MEIPASS (onefile) ou diretório do executável (one-folder)
    BASE_DIR = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
else:
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

# Diretório de dados (padrão: data/ na raiz do projeto ou junto ao executável)
PROJECT_ROOT = BASE_DIR
DATA_DIR = os.getenv("DATA_DIR", os.path.join(PROJECT_ROOT, "data"))

os.makedirs(DATA_DIR, exist_ok=True)

EXPENSES_FILE = os.path.join(DATA_DIR, "expenses.json")
REVENUES_FILE = os.path.join(DATA_DIR, "revenues.json")
DB_FILE = os.path.join(DATA_DIR, "mymoney.db")
ICONS_DIR = os.path.join(PROJECT_ROOT, "app", "ui", "assets", "icons")
# Em ambiente de desenvolvimento, garante a existência do diretório de ícones;
# em binários empacotados, os arquivos são incluídos via PyInstaller e não devem ser criados.
if not getattr(sys, 'frozen', False):
    os.makedirs(ICONS_DIR, exist_ok=True)