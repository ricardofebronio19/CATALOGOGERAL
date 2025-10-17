import os
import sys

# Garante que o diretório raiz do projeto está no sys.path para importar app/models
PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app import create_app, db
from models import Produto, Aplicacao

app = create_app()

with app.app_context():
    # Cria um produto de teste
    p = Produto(nome='TESTE AUTOMATIZADO', codigo='TESTE-123')
    db.session.add(p)
    db.session.flush()

    # Simula dados de form onde 'id' é string vazia
    data = {'id': '', 'veiculo': 'AMAROK', 'ano': '2010/...', 'motor': '2.0 16V', 'conf_mtr': '', 'montadora': 'VOLKSWAGEN'}
    # Filtra id antes de criar (mesma lógica aplicada em routes.py)
    filtered = {k: v for k, v in data.items() if k != 'id'}
    a = Aplicacao(produto=p, **filtered)
    db.session.add(a)

    try:
        db.session.commit()
        print('Produto e aplicação criados com sucesso. Produto id:', p.id, 'Aplicacao id:', a.id)
    except Exception as e:
        db.session.rollback()
        print('Erro ao criar:', e)
