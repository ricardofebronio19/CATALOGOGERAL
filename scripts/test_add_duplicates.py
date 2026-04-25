from app import create_app, db
from models import Produto

app = create_app()

with app.app_context():
    # Limpa produtos de teste se existirem
    db.session.query(Produto).filter(Produto.codigo=='TESTDUP').delete()
    db.session.commit()

    p1 = Produto(nome='Teste 1', codigo='TESTDUP', fornecedor='FORNEC_A')
    p2 = Produto(nome='Teste 2', codigo='TESTDUP', fornecedor='FORNEC_B')
    db.session.add(p1)
    db.session.add(p2)
    try:
        db.session.commit()
        print('Sucesso: inseridos dois produtos com mesmo código e fornecedores diferentes')
    except Exception as e:
        db.session.rollback()
        print('Falha ao inserir:', e)
