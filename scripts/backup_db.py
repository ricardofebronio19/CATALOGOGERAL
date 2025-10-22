import datetime
import os
import shutil
import sys

# Garante que o diretório do projeto esteja no sys.path para importar módulos locais
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


def main():
    import app

    dbpath = os.path.join(app.APP_DATA_PATH, "catalogo.db")
    if not os.path.exists(dbpath):
        print("AVISO: banco de dados não existe em", dbpath)
    else:
        bak = dbpath + "." + datetime.datetime.now().strftime("%Y%m%d%H%M%S") + ".bak"
        shutil.copy2(dbpath, bak)
        print("Backup criado:", bak)


if __name__ == "__main__":
    main()
