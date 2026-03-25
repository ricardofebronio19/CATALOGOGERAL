from app import create_app, db
from sqlalchemy import text

app = create_app()

with app.app_context():
    engine = db.engine
    conn = engine.connect()
    trans = conn.begin()
    try:
        print("Desabilitando foreign_keys e preparando tabelas antigas...")
        conn.execute(text("PRAGMA foreign_keys=OFF;"))
        # Remove uma tabela temporária antiga, se existir
        conn.execute(text("DROP TABLE IF EXISTS produto_old;"))
        conn.execute(text("ALTER TABLE produto RENAME TO produto_old;"))

        print("Removendo índices antigos que podem conflitar...")
        conn.execute(text("DROP INDEX IF EXISTS ix_produto_fornecedor;"))
        conn.execute(text("DROP INDEX IF EXISTS ix_produto_codigo;"))
        conn.execute(text("DROP INDEX IF EXISTS ix_produto_grupo;"))

        print("Criando nova tabela 'produto' a partir dos modelos...")
        db.create_all()

        cols = [
            "id",
            "nome",
            "codigo",
            "grupo",
            "fornecedor",
            "conversoes",
            "medidas",
            "observacoes",
        ]
        cols_str = ",".join(cols)
        print("Copiando dados de produto_old para produto...")
        conn.execute(text(f"INSERT INTO produto ({cols_str}) SELECT {cols_str} FROM produto_old;"))

        print("Removendo tabela produto_old...")
        conn.execute(text("DROP TABLE produto_old;"))

        conn.execute(text("PRAGMA foreign_keys=ON;"))
        trans.commit()
        print("Migração concluída com sucesso.")
    except Exception as e:
        trans.rollback()
        print("Erro durante migração:", e)
