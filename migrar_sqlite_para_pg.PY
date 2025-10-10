import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager

# Importa os modelos e as configurações da sua aplicação principal
from app import db, Produto, Aplicacao, ImagemProduto, User, APP_DATA_PATH

# --- CONFIGURAÇÕES DE CONEXÃO ---

# 1. Conexão com o banco de dados ANTIGO (SQLite)
# O script vai procurar o arquivo catalogo.db na sua pasta de dados
SQLITE_DB_PATH = os.path.join(APP_DATA_PATH, "catalogo.db")
if not os.path.exists(SQLITE_DB_PATH):
    print(f"ERRO: Banco de dados SQLite não encontrado em '{SQLITE_DB_PATH}'")
    exit()
sqlite_engine = create_engine(f'sqlite:///{SQLITE_DB_PATH}')

# 2. Conexão com o banco de dados NOVO (PostgreSQL)
# IMPORTANTE: Use a mesma string de conexão que você configurou no app.py
# Exemplo: 'postgresql://usuario_catalogo:senha_segura@ip_do_servidor/catalogo_db'
POSTGRES_CONN_STR = 'postgresql://usuario_catalogo:senha_segura@localhost/catalogo_db'
postgres_engine = create_engine(POSTGRES_CONN_STR)

# --- SESSÕES DE BANCO DE DADOS ---

# Cria "fábricas" de sessão para cada banco de dados
SQLiteSession = sessionmaker(bind=sqlite_engine)
PostgresSession = sessionmaker(bind=postgres_engine)

@contextmanager
def session_scope(session_factory):
    """Fornece um escopo transacional para uma sessão."""
    session = session_factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

def migrar_dados():
    """
    Função principal que executa a migração dos dados.
    """
    print("Iniciando a migração de dados de SQLite para PostgreSQL...")
    print("Este processo pode levar alguns minutos, dependendo do tamanho do seu banco de dados.")

    # Garante que as tabelas existam no banco de destino (PostgreSQL)
    print("\n1. Verificando e criando tabelas no PostgreSQL (se necessário)...")
    db.metadata.create_all(bind=postgres_engine)
    print("   Tabelas verificadas.")

    # Dicionários para mapear IDs antigos para novos
    # Isso é essencial para recriar os relacionamentos corretamente
    produtos_id_map = {}

    with session_scope(SQLiteSession) as sqlite_session, session_scope(PostgresSession) as pg_session:
        
        # --- Migração de Usuários ---
        print("\n2. Migrando usuários...")
        usuarios_sqlite = sqlite_session.query(User).all()
        for usuario_antigo in usuarios_sqlite:
            # Verifica se o usuário já existe no destino
            usuario_novo = pg_session.query(User).filter_by(username=usuario_antigo.username).first()
            if not usuario_novo:
                usuario_novo = User(
                    username=usuario_antigo.username,
                    password_hash=usuario_antigo.password_hash,
                    is_admin=usuario_antigo.is_admin
                )
                pg_session.add(usuario_novo)
        pg_session.commit() # Salva os usuários para que tenham IDs
        print(f"   {len(usuarios_sqlite)} usuários migrados.")

        # --- Migração de Produtos, Imagens e Aplicações ---
        print("\n3. Migrando produtos, imagens e aplicações...")
        produtos_sqlite = sqlite_session.query(Produto).all()
        
        for i, produto_antigo in enumerate(produtos_sqlite, 1):
            print(f"   Processando produto {i}/{len(produtos_sqlite)}: {produto_antigo.codigo}")
            
            # Verifica se o produto já existe no destino
            produto_novo = pg_session.query(Produto).filter_by(codigo=produto_antigo.codigo).first()
            if not produto_novo:
                produto_novo = Produto(
                    nome=produto_antigo.nome,
                    codigo=produto_antigo.codigo,
                    grupo=produto_antigo.grupo,
                    fornecedor=produto_antigo.fornecedor,
                    conversoes=produto_antigo.conversoes,
                    medidas=produto_antigo.medidas,
                    observacoes=produto_antigo.observacoes
                )
                
                # Copia as aplicações
                for app_antiga in produto_antigo.aplicacoes:
                    produto_novo.aplicacoes.append(Aplicacao(
                        veiculo=app_antiga.veiculo,
                        ano=app_antiga.ano,
                        motor=app_antiga.motor,
                        conf_mtr=app_antiga.conf_mtr,
                        montadora=app_antiga.montadora
                    ))

                # Copia as imagens
                for img_antiga in produto_antigo.imagens:
                    produto_novo.imagens.append(ImagemProduto(
                        filename=img_antiga.filename,
                        ordem=img_antiga.ordem
                    ))
                
                pg_session.add(produto_novo)
                pg_session.flush() # Força a inserção para obter o novo ID
            
            # Mapeia o ID antigo para o novo ID
            produtos_id_map[produto_antigo.id] = produto_novo.id

        pg_session.commit()
        print("   Produtos, imagens e aplicações migrados.")

        # --- Migração de Relacionamentos de Similares ---
        print("\n4. Migrando relacionamentos de similares...")
        produtos_sqlite = sqlite_session.query(Produto).all()
        similares_migrados = 0
        for produto_antigo in produtos_sqlite:
            if not produto_antigo.similares:
                continue

            # Pega o produto correspondente no novo banco
            id_novo_produto_principal = produtos_id_map.get(produto_antigo.id)
            if not id_novo_produto_principal: continue
            
            produto_principal_novo = pg_session.get(Produto, id_novo_produto_principal)
            
            # Encontra os similares correspondentes no novo banco
            for similar_antigo in produto_antigo.similares:
                id_novo_similar = produtos_id_map.get(similar_antigo.id)
                if not id_novo_similar: continue
                
                similar_novo = pg_session.get(Produto, id_novo_similar)
                
                # Adiciona a relação se ainda não existir
                if similar_novo not in produto_principal_novo.similares:
                    produto_principal_novo.similares.append(similar_novo)
                    similares_migrados += 1
        
        pg_session.commit()
        print(f"   {similares_migrados} relações de similaridade migradas.")

    print("\n--- MIGRAÇÃO CONCLUÍDA COM SUCESSO! ---")
    print("Você já pode iniciar a aplicação normalmente com 'python run.py'.")

if __name__ == '__main__':
    migrar_dados()
