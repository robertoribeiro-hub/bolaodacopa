import os
import json
from pathlib import Path

# Importa `load_dotenv` de forma resiliente: em ambientes onde
# `python-dotenv` não está instalado, não interrompemos a inicialização
try:
    from dotenv import load_dotenv
except Exception:
    def load_dotenv(*args, **kwargs):
        # fallback vazio quando python-dotenv não estiver disponível
        return False

# Caminho raiz do projeto
BASE_DIR = Path(__file__).resolve().parent.parent

# Carrega as variáveis de ambiente do arquivo .env
ENV_FILE = BASE_DIR / ".env"
if ENV_FILE.exists():
    load_dotenv(dotenv_path=ENV_FILE)

# Configurações do DaCopa
DACOPA_BASE_URL = os.getenv("DACOPA_BASE_URL", "https://app.dacopa.com")
DACOPA_EMAIL = os.getenv("DACOPA_EMAIL", "")
DACOPA_PASSWORD = os.getenv("DACOPA_PASSWORD", "")
DACOPA_GROUP_ID = os.getenv("DACOPA_GROUP_ID", "")
HEADLESS = os.getenv("HEADLESS", "True").lower() in ("true", "1", "yes")

# Caminhos de diretórios úteis
STORAGE_DIR = BASE_DIR / "storage"
LOGS_DIR = BASE_DIR / "logs"
CONFIG_DIR = BASE_DIR / "config"
ASSETS_DIR = BASE_DIR / "assets"

# Caminhos de arquivos específicos
MEMBROS_EXCEL = STORAGE_DIR / "membros.xlsx"
HISTORICO_EXCEL = STORAGE_DIR / "historico.xlsx"
PALPITES_EXCEL = STORAGE_DIR / "palpites.xlsx"
AUTH_STATE_FILE = STORAGE_DIR / "auth_state.json"
SELECTORS_JSON = CONFIG_DIR / "selectors.json"
LOG_COLLECTOR_FILE = LOGS_DIR / "collector.log"
LOG_APP_FILE = LOGS_DIR / "app.log"

# Garante que os diretórios necessários existem
STORAGE_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Carrega os seletores CSS
def get_selectors() -> dict:
    if SELECTORS_JSON.exists():
        try:
            with open(SELECTORS_JSON, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Erro ao ler selectors.json: {e}")
            return {}
    return {}

SELECTORS = get_selectors()
