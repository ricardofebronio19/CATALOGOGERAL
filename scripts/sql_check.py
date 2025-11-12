import os, sqlite3
appdata = os.getenv('APPDATA') or os.path.expanduser('~')
db_path = os.path.join(appdata, 'CatalogoDePecas', 'catalogo.db')
conn = sqlite3.connect(db_path)
c = conn.cursor()
sql = """SELECT produto.id, produto.codigo, produto.nome FROM produto JOIN aplicacao ON produto.id = aplicacao.produto_id
WHERE lower(aplicacao.montadora) LIKE lower('%Citroën%') AND (lower(aplicacao.veiculo) LIKE lower('%BERLINGO%') OR lower(aplicacao.motor) LIKE lower('%BERLINGO%'))
GROUP BY produto.id
"""
print(sql)
for row in c.execute(sql):
    print(row)
conn.close()
