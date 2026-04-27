import sqlite3
db = r'C:\Users\ricar\AppData\Roaming\CatalogoDePecas\catalogo.db'
conn = sqlite3.connect(db)
tabs = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
print('Tabelas:', tabs)
if 'produto' in tabs:
    print('Produtos:', conn.execute('SELECT COUNT(*) FROM produto').fetchone()[0])
conn.close()
print('OK')
