import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import create_app


def test_detalhe_peca_renders_successfully():
    app = create_app()
    app.config.update(TESTING=True)

    with app.test_client() as client:
        response = client.get('/peca/16570')

    assert response.status_code == 200
