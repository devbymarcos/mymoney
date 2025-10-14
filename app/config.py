import os
from dotenv import load_dotenv

load_dotenv()

APP_NAME = os.getenv("APP_NAME", "Mymoney")

# Diretório de dados (padrão: data/ na raiz do projeto)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
DATA_DIR = os.getenv("DATA_DIR", os.path.join(PROJECT_ROOT, "data"))

os.makedirs(DATA_DIR, exist_ok=True)

EXPENSES_FILE = os.path.join(DATA_DIR, "expenses.json")
REVENUES_FILE = os.path.join(DATA_DIR, "revenues.json")
DB_FILE = os.path.join(DATA_DIR, "mymoney.db")
ICONS_DIR = os.path.join(PROJECT_ROOT, "app", "ui", "assets", "icons")
os.makedirs(ICONS_DIR, exist_ok=True)