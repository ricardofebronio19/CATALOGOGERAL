import importlib
import os
import shutil
import tempfile
import time


def test_adicionar_peca_com_id_vazio_cria_aplicacao():
    # Cria um app em um diretório temporário para isolar o DB/uploads
    td = tempfile.mkdtemp()
    try:
        # Importa o módulo app e ajusta APP_DATA_PATH antes de criar a app
        import app as appmodule

        importlib.reload(appmodule)

        # Ajusta paths para o ambiente de teste
        appmodule.APP_DATA_PATH = td
        appmodule.UPLOAD_FOLDER = os.path.join(td, "uploads")
        os.makedirs(appmodule.UPLOAD_FOLDER, exist_ok=True)

        # Cria a app
        app = appmodule.create_app()
        app.config["TESTING"] = True

        from app import db
        from models import Produto, User

        try:
            with app.app_context():
                # Reinicia o banco para o teste
                db.drop_all()
                db.create_all()

                # Cria um usuário administrador de teste
                test_admin = User(username="testadmin", is_admin=True)
                test_admin.set_password("pass")
                db.session.add(test_admin)
                db.session.commit()

                client = app.test_client()

                # Login
                resp = client.post(
                    "/login",
                    data={"username": "testadmin", "password": "pass"},
                    follow_redirects=True,
                )
                assert resp.status_code == 200

                # Envia formulário de adicionar peça com aplicacao contendo id vazio
                form = {
                    "nome": "Teste Produto",
                    "codigo": "COD123TEST",
                    "grupo": "GRUPO1",
                    "fornecedor": "FORN1",
                    "conversoes": "",
                    "medidas": "",
                    "observacoes": "",
                    "aplicacoes-0-id": "",
                    "aplicacoes-0-veiculo": "VEIC1",
                    "aplicacoes-0-ano": "2010",
                    "aplicacoes-0-motor": "MTR1",
                    "aplicacoes-0-conf_mtr": "",
                    "aplicacoes-0-montadora": "MONT1",
                }

                resp = client.post(
                    "/admin/peca/adicionar", data=form, follow_redirects=True
                )
                assert resp.status_code == 200

                # Valida no DB
                p = Produto.query.filter_by(codigo="COD123TEST").first()
                assert p is not None
                assert len(p.aplicacoes) == 1
                assert p.aplicacoes[0].veiculo == "VEIC1"
        finally:
            # Fecha a sessão e dispõe o engine para liberar o arquivo do sqlite no Windows
            try:
                db.session.remove()
            except Exception:
                pass
            try:
                db.engine.dispose()
            except Exception:
                pass
    finally:
        # Tenta remover o diretório temporário com retries (Windows pode manter lock por pouco tempo)
        for i in range(5):
            try:
                shutil.rmtree(td)
                break
            except PermissionError:
                time.sleep(0.2)
        else:
            # última tentativa sem levantar
            try:
                shutil.rmtree(td)
            except Exception:
                pass
