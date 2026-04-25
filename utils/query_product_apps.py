"""Consulta aplicações de um produto pelo `codigo` e imprime resultados.
Uso:
  python utils/query_product_apps.py 18264
Se nenhum código for passado, verifica `18264` por padrão.
"""
import sys
import os

# Garantir que o diretório do projeto esteja no sys.path
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app import create_app, db
from models import Produto

app = create_app()


def query(codigo='18264'):
    with app.app_context():
        p = Produto.query.filter_by(codigo=str(codigo)).first()
        if not p:
            print(f"Produto com codigo={codigo} não encontrado")
            return
        print(f"Produto: id={p.id} codigo={p.codigo} nome={p.nome}")
        print(f"Aplicacoes ({len(p.aplicacoes)}):")
        for a in p.aplicacoes[:50]:
            print(f" - veiculo={a.veiculo!r} | ano={a.ano!r} | montadora={a.montadora!r} | motor={a.motor!r}")


if __name__ == '__main__':
    codigo = sys.argv[1] if len(sys.argv) > 1 else '18264'
    query(codigo)
