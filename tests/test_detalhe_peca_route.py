import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import app as app_module
from app import create_app, db, inicializar_banco
from models import Aplicacao, Produto, User


def test_detalhe_peca_renders_successfully():
    app = create_app()
    app.config.update(TESTING=True)

    with app.test_client() as client:
        response = client.get('/peca/16570')

    assert response.status_code == 200


def test_clonar_peca_copies_applications(tmp_path):
    app_module.APP_DATA_PATH = str(tmp_path)
    app_module.UPLOAD_FOLDER = str(tmp_path / "uploads")
    app_module.CONFIG_FILE = str(tmp_path / "config.json")
    os.makedirs(app_module.UPLOAD_FOLDER, exist_ok=True)

    app = create_app()
    app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)

    with app.app_context():
        inicializar_banco(app)

        admin = User(username="admin-clone", is_admin=True)
        admin.set_password("secret123")
        db.session.add(admin)
        db.session.commit()

        produto_original = Produto(
            nome="Peça Original",
            codigo="ABC123",
            fornecedor="FORN",
            grupo="GRUPO",
            conversoes="conv",
            medidas="med",
            observacoes="obs",
        )
        db.session.add(produto_original)
        db.session.flush()

        aplicacao = Aplicacao(
            produto_id=produto_original.id,
            veiculo="Civic",
            ano="2020",
            motor="1.8",
            conf_mtr="Flex",
            montadora="Honda",
        )
        db.session.add(aplicacao)
        db.session.commit()

    with app.test_client() as client:
        login_response = client.post(
            "/login",
            data={"username": "admin-clone", "password": "secret123"},
            follow_redirects=False,
        )
        assert login_response.status_code == 302

        clone_response = client.get(
            f"/peca/{produto_original.id}/clonar",
            follow_redirects=False,
        )

    with app.app_context():
        produto_clonado = (
            Produto.query.filter(Produto.codigo.startswith("ABC123-"))
            .order_by(Produto.id.desc())
            .first()
        )

    assert clone_response.status_code == 302
    assert produto_clonado is not None
    assert len(produto_clonado.aplicacoes) == 1
    assert produto_clonado.aplicacoes[0].veiculo == "Civic"
