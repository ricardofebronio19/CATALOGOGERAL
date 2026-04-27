import importlib
import os
import shutil
import sys
import tempfile

# Garante que o diretório raiz do projeto está no sys.path para importar app/models
PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


def main():
    import app as appmodule

    importlib.reload(appmodule)

    # Usa um diretório temporário para isolar o banco de dados durante este script
    td = tempfile.mkdtemp()
    try:
        appmodule.APP_DATA_PATH = td
        appmodule.UPLOAD_FOLDER = os.path.join(td, "uploads")
        os.makedirs(appmodule.UPLOAD_FOLDER, exist_ok=True)

        from app import create_app, db
        from models import Aplicacao, Produto

        app = create_app()

        with app.app_context():
            # Garante banco limpo
            db.drop_all()
            db.create_all()

            # Cria um produto de teste
            p = Produto(nome="TESTE AUTOMATIZADO", codigo="TESTE-123")
            db.session.add(p)
            db.session.flush()

            # Simula dados de form onde 'id' é string vazia
            data = {
                "id": "",
                "veiculo": "AMAROK",
                "ano": "2010/...",
                "motor": "2.0 16V",
                "conf_mtr": "",
                "montadora": "VOLKSWAGEN",
            }
            # Filtra id antes de criar (mesma lógica aplicada em routes.py)
            filtered = {k: v for k, v in data.items() if k != "id"}
            a = Aplicacao(produto=p, **filtered)
            db.session.add(a)

            try:
                db.session.commit()
                print(
                    "Produto e aplicação criados com sucesso. Produto id:",
                    p.id,
                    "Aplicacao id:",
                    a.id,
                )
            except Exception as e:
                db.session.rollback()
                print("Erro ao criar:", e)
    finally:
        # Limpa o diretório temporário
        try:
            shutil.rmtree(td)
        except Exception:
            pass


if __name__ == "__main__":
    main()
