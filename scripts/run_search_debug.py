import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import create_app, db
from core_utils import _build_search_query

app = create_app()
with app.app_context():
    montadora = 'Citroën'
    aplicacao = 'BERLINGO'
    # Show normalization used by _build_search_query
    from core_utils import _normalize_for_search
    print('montadora raw:', montadora)
    print('montadora normalized:', _normalize_for_search(montadora))
    query = _build_search_query('', '', montadora, aplicacao, '', '')
    # Debug: print SQL representation (may contain parameters)
    try:
        print('\nQuery repr:', query)
        print('\nQuery statement:', query.statement)
    except Exception as e:
        print('Could not print query statement:', e)
    # Try compiling SQL with literal binds for inspection
    try:
        compiled = query.statement.compile(compile_kwargs={"literal_binds": True}, dialect=db.session.bind.dialect)
        print('\nCompiled SQL with literal binds:\n', compiled)
    except Exception as e:
        print('Could not compile SQL with literal binds:', e)

    # Ensure distinct
    results = query.distinct().all()
    print('Found', len(results), 'products')
    for p in results[:50]:
        print(p.id, p.codigo, p.nome)

    # Cross-check: fetch product ids from aplicacao table directly
    from models import Aplicacao, Produto
    prod_ids = [r[0] for r in db.session.query(Aplicacao.produto_id).filter(Aplicacao.veiculo.ilike('%BERLINGO%')).distinct().all()]
    print('\nProducto IDs referenced by aplicacoes with BERLINGO:', prod_ids[:50])
    if prod_ids:
        prods = Produto.query.filter(Produto.id.in_(prod_ids)).all()
        print('Found products by direct lookup:', len(prods))
        for p in prods[:20]:
            print(p.id, p.codigo, p.nome)

    # Try querying Aplicacao via SQLAlchemy using ilike
    apps = db.session.query(Aplicacao).filter(Aplicacao.montadora.ilike('%Citroën%'), Aplicacao.veiculo.ilike('%BERLINGO%')).all()
    print('\nAplicacoes via SQLAlchemy ilike count:', len(apps))
    for a in apps[:20]:
        print(a.id, a.produto_id, a.montadora, a.veiculo, a.motor)
