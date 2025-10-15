import os
import shutil
from pathlib import Path

# Local relativo dentro do projeto
PROJECT_ROOT = Path(__file__).resolve().parents[1]
# Caminho esperável do banco no APP_DATA_PATH (conforme app.py) ou em local padrão
APP_DATA_PATH = os.environ.get('APP_DATA_PATH')
if not APP_DATA_PATH:
    # fallback para %APPDATA%/CatalogoDePecas
    APP_DATA_PATH = os.path.join(os.environ.get('APPDATA', ''), 'CatalogoDePecas')

source_db = Path(APP_DATA_PATH) / 'catalogo.db'

target_dir = PROJECT_ROOT / 'data'
target_db = target_dir / 'catalogo.db'

if not source_db.exists():
    print(f"Nenhum banco encontrado em: {source_db}")
    raise SystemExit(1)

if not target_dir.exists():
    target_dir.mkdir(parents=True)

shutil.copy2(source_db, target_db)
print(f"Banco copiado para: {target_db}")
