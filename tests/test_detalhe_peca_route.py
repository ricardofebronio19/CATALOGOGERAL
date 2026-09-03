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


def test_detalhe_peca_aplica_scroll_no_bloco_conversoes():
    css_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'style.css')

    with open(css_path, encoding='utf-8') as css_file:
        css_content = css_file.read()

    assert 'max-height: 320px' in css_content
    assert 'overflow-y: auto' in css_content


def test_observacoes_with_url_are_rendered_as_links():
    app = create_app()
    app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)

    with app.app_context():
        inicializar_banco(app)

        produto = Produto(
            nome="Peça com Link",
            codigo="LINK001",
            fornecedor="FORN",
            grupo="GRUPO",
            observacoes="Veja o catálogo em https://exemplo.com/catalogo",
        )
        db.session.add(produto)
        db.session.commit()

    with app.test_client() as client:
        response = client.get(f"/peca/{produto.id}")

    assert response.status_code == 200
    assert b'href="https://exemplo.com/catalogo"' in response.data
    assert b'target="_blank"' in response.data


def test_observacoes_with_product_code_are_rendered_as_internal_links():
    app = create_app()
    app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)

    with app.app_context():
        inicializar_banco(app)

        produto_relacionado = Produto(
            nome="Peça Destino",
            codigo="123456",
            fornecedor="FORN",
            grupo="GRUPO",
        )
        db.session.add(produto_relacionado)
        db.session.flush()

        produto_origem = Produto(
            nome="Peça Origem",
            codigo="ORIG001",
            fornecedor="FORN",
            grupo="GRUPO",
            observacoes="Compatível com 123456",
        )
        db.session.add(produto_origem)
        db.session.commit()

        produto_origem_id = produto_origem.id
        produto_relacionado_id = produto_relacionado.id

    with app.test_client() as client:
        response = client.get(f"/peca/{produto_origem_id}")

    assert response.status_code == 200
    assert f'href="/peca/{produto_relacionado_id}"'.encode() in response.data
    assert b">123456</a>" in response.data


def test_create_app_creates_missing_data_directory_before_writing_config(tmp_path):
    app_module.APP_DATA_PATH = str(tmp_path / "missing" / "CatalogoDePecas")
    app_module.UPLOAD_FOLDER = str(tmp_path / "missing" / "CatalogoDePecas" / "uploads")
    app_module.CONFIG_FILE = str(tmp_path / "missing" / "CatalogoDePecas" / "config.json")

    app = create_app()

    assert os.path.exists(app_module.APP_DATA_PATH)
    assert os.path.exists(app_module.CONFIG_FILE)
    assert app.config["SECRET_KEY"]


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
