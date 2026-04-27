import os
import sqlite3
import sys
appdata = os.getenv('APPDATA') or os.path.expanduser('~')
db_path = os.path.join(appdata, 'CatalogoDePecas', 'catalogo.db')
print('DB path:', db_path)
if not os.path.exists(db_path):
    print('Database not found')
    sys.exit(0)
conn = sqlite3.connect(db_path)
c = conn.cursor()
print('\nDistinct montadora values containing citro')
for row in c.execute("SELECT DISTINCT montadora FROM aplicacao WHERE lower(montadora) LIKE '%citro%'"):
    print(row)
print('\nRows where veiculo LIKE %BERLINGO%:')
for row in c.execute("SELECT id, produto_id, montadora, veiculo, motor FROM aplicacao WHERE upper(veiculo) LIKE '%BERLINGO%' LIMIT 50"):
    print(row)
print('\nSample aplicacao rows for montadora Citroen variants:')
for row in c.execute("SELECT id, produto_id, montadora, veiculo, motor FROM aplicacao WHERE lower(montadora) LIKE '%citroen%' LIMIT 50"):
    print(row)
conn.close()
