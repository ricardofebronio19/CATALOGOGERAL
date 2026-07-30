"""Script para recuperar o banco de dados do arquivo de backup zip."""
import os
import shutil
import sqlite3
import sys
import tempfile
import zipfile

BACKUP_DIR = r"C:\Users\ricar\AppData\Roaming\CatalogoDePecas_old_1777068510.7346997"
DATA_PATH = r"C:\Users\ricar\AppData\Roaming\CatalogoDePecas"
ZIP_PATH = os.path.join(BACKUP_DIR, "backup_para_restaurar.zip")
DB_DEST = os.path.join(DATA_PATH, "catalogo.db")

# 1. Verifica o DB atual (corrompido)
print(f"DB atual ({os.path.getsize(DB_DEST)} bytes) - verificando integridade...")
try:
    conn = sqlite3.connect(DB_DEST)
    conn.execute("PRAGMA integrity_check").fetchone()
    print("DB atual está OK!")
    conn.close()
    sys.exit(0)
except Exception as e:
    print(f"DB atual corrompido: {e}")
    conn.close()

# 2. Tenta extrair o DB do zip de backup
print(f"\nExtrahindo DB do backup zip ({os.path.getsize(ZIP_PATH)//1024//1024} MB)...")
tmp_dir = tempfile.mkdtemp(prefix="catalogo_recover_")
try:
    with zipfile.ZipFile(ZIP_PATH, "r") as zf:
        members = zf.namelist()
        db_members = [m for m in members if m.endswith("catalogo.db")]
        print(f"Arquivos DB no zip: {db_members}")
        
        if not db_members:
            print("AVISO: Nenhum catalogo.db encontrado no zip!")
            # Lista todos os arquivos
            print("Arquivos no zip:", members[:20])
            sys.exit(1)
        
        # Extrai o primeiro DB encontrado
        db_member = db_members[0]
        zf.extract(db_member, tmp_dir)
        extracted_db = os.path.join(tmp_dir, db_member)
        
        # Verifica integridade do DB extraído
        print(f"Verificando integridade do DB extraído...")
        conn2 = sqlite3.connect(extracted_db)
        result = conn2.execute("PRAGMA integrity_check").fetchone()
        tabs = [r[0] for r in conn2.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
        prod_count = conn2.execute("SELECT COUNT(*) FROM produto").fetchone()[0]
        conn2.close()
        print(f"Integridade: {result[0]}")
        print(f"Tabelas: {tabs}")
        print(f"Produtos: {prod_count}")
        
        if result[0] == "ok":
            # Substitui o DB corrompido
            bak = DB_DEST + ".corrupted.bak"
            shutil.copy2(DB_DEST, bak)
            print(f"\nBackup do DB corrompido salvo em: {bak}")
            shutil.copy2(extracted_db, DB_DEST)
            print(f"DB restaurado com sucesso! ({prod_count} produtos)")
        else:
            print("ERRO: DB do zip também tem problemas de integridade!")
finally:
    shutil.rmtree(tmp_dir, ignore_errors=True)
