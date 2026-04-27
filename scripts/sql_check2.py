import os, sqlite3
appdata = os.getenv('APPDATA') or os.path.expanduser('~')
db_path = os.path.join(appdata, 'CatalogoDePecas', 'catalogo.db')
conn = sqlite3.connect(db_path)
c = conn.cursor()
print('Count aplicacao rows where montadora lower like %citro%:')
for row in c.execute("SELECT count(*) FROM aplicacao WHERE lower(montadora) LIKE '%citro%'"):
    print(row)
print('Count aplicacao where veiculo like %BERLINGO%:')
for row in c.execute("SELECT count(*) FROM aplicacao WHERE upper(veiculo) LIKE '%BERLINGO%'"):
    print(row)
print('Count both conditions:')
for row in c.execute("SELECT count(*) FROM aplicacao WHERE lower(montadora) LIKE '%citro%' AND upper(veiculo) LIKE '%BERLINGO%'"):
    print(row)
print('Sample rows matching both conditions:')
for row in c.execute("SELECT id, produto_id, montadora, veiculo, motor FROM aplicacao WHERE lower(montadora) LIKE '%citro%' AND upper(veiculo) LIKE '%BERLINGO%' LIMIT 20"):
    print(row)
conn.close()
