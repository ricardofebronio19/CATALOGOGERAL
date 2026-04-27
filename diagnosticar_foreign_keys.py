#!/usr/bin/env python3
"""
Script de diagnóstico para identificar problemas de foreign key
entre compartilhamento_lista e user
"""

import os
import sys
import sqlite3
from datetime import datetime

# Adiciona o diretório atual ao path para importar os modelos
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def setup_app():
    """Configura o app Flask para acesso aos modelos"""
    from app import app, db
    with app.app_context():
        return app, db

def diagnosticar_foreign_keys():
    """Identifica problemas de foreign key na tabela compartilhamento_lista"""
    app, db = setup_app()
    
    print("=" * 60)
    print("DIAGNÓSTICO DE FOREIGN KEY MISMATCH")
    print("=" * 60)
    print(f"Iniciado em: {datetime.now()}")
    print()
    
    # Conecta diretamente ao SQLite para fazer queries raw
    db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'catalogo.db')
    if not os.path.exists(db_path):
        # Tenta localizar o banco na pasta atual
        db_path = 'catalogo.db'
        if not os.path.exists(db_path):
            print("❌ ERRO: Banco de dados não encontrado!")
            return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Verifica se as tabelas existem
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name IN ('user', 'compartilhamento_lista')
        """)
        tables = [row[0] for row in cursor.fetchall()]
        
        print("📋 TABELAS ENCONTRADAS:")
        for table in tables:
            print(f"   ✓ {table}")
        
        if 'user' not in tables:
            print("❌ Tabela 'user' não encontrada!")
            return False
            
        if 'compartilhamento_lista' not in tables:
            print("❌ Tabela 'compartilhamento_lista' não encontrada!")
            return False
        
        print()
        
        # Conta registros nas tabelas
        cursor.execute("SELECT COUNT(*) FROM user")
        user_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM compartilhamento_lista")
        compartilhamento_count = cursor.fetchone()[0]
        
        print("📊 ESTATÍSTICAS:")
        print(f"   Usuários: {user_count}")
        print(f"   Compartilhamentos: {compartilhamento_count}")
        print()
        
        if compartilhamento_count == 0:
            print("✅ Nenhum compartilhamento encontrado - sem problemas de FK")
            return True
        
        # Verifica IDs de usuários existentes
        cursor.execute("SELECT id FROM user ORDER BY id")
        user_ids = set(row[0] for row in cursor.fetchall())
        print(f"   IDs de usuários válidos: {sorted(user_ids)}")
        print()
        
        # Identifica registros problemáticos - compartilhado_por órfão
        print("🔍 VERIFICANDO FOREIGN KEYS ÓRFÃOS:")
        
        cursor.execute("""
            SELECT id, lista_id, compartilhado_por, compartilhado_com, criado_em
            FROM compartilhamento_lista 
            WHERE compartilhado_por NOT IN (SELECT id FROM user)
        """)
        problemas_por = cursor.fetchall()
        
        # Identifica registros problemáticos - compartilhado_com órfão
        cursor.execute("""
            SELECT id, lista_id, compartilhado_por, compartilhado_com, criado_em
            FROM compartilhamento_lista 
            WHERE compartilhado_com NOT IN (SELECT id FROM user)
        """)
        problemas_com = cursor.fetchall()
        
        print(f"   Registros com 'compartilhado_por' órfão: {len(problemas_por)}")
        print(f"   Registros com 'compartilhado_com' órfão: {len(problemas_com)}")
        
        # Mostra detalhes dos problemas
        if problemas_por:
            print("\n❌ PROBLEMAS COM 'compartilhado_por':")
            for reg in problemas_por:
                print(f"   ID: {reg[0]}, Lista: {reg[1]}, Por: {reg[2]} (ÓRFÃO), Com: {reg[3]}, Data: {reg[4]}")
        
        if problemas_com:
            print("\n❌ PROBLEMAS COM 'compartilhado_com':")
            for reg in problemas_com:
                print(f"   ID: {reg[0]}, Lista: {reg[1]}, Por: {reg[2]}, Com: {reg[3]} (ÓRFÃO), Data: {reg[4]}")
        
        # Verifica se existem registros com ambos os campos órfãos
        cursor.execute("""
            SELECT id, lista_id, compartilhado_por, compartilhado_com, criado_em
            FROM compartilhamento_lista 
            WHERE compartilhado_por NOT IN (SELECT id FROM user)
            AND compartilhado_com NOT IN (SELECT id FROM user)
        """)
        problemas_duplos = cursor.fetchall()
        
        if problemas_duplos:
            print(f"\n❌❌ REGISTROS COM AMBOS CAMPOS ÓRFÃOS: {len(problemas_duplos)}")
            for reg in problemas_duplos:
                print(f"   ID: {reg[0]}, Lista: {reg[1]}, Por: {reg[2]} (ÓRFÃO), Com: {reg[3]} (ÓRFÃO), Data: {reg[4]}")
        
        # Resumo
        total_problemas = len(set([r[0] for r in problemas_por] + [r[0] for r in problemas_com]))
        
        print(f"\n📊 RESUMO DO DIAGNÓSTICO:")
        print(f"   Total de registros problemáticos: {total_problemas}")
        
        if total_problemas > 0:
            print("❌ AÇÃO NECESSÁRIA: Existem registros com foreign keys órfãos!")
            print("   Execute o script de correção para resolver o problema.")
            return False
        else:
            print("✅ BANCO ÍNTEGRO: Nenhum problema de foreign key encontrado!")
            return True
        
    except Exception as e:
        print(f"❌ ERRO durante diagnóstico: {e}")
        return False
    finally:
        conn.close()

def testar_backup():
    """Testa se o iterdump() funciona após verificar foreign keys"""
    print("\n" + "=" * 60)
    print("TESTE DE BACKUP (iterdump)")
    print("=" * 60)
    
    db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'catalogo.db')
    if not os.path.exists(db_path):
        db_path = 'catalogo.db'
        if not os.path.exists(db_path):
            print("❌ ERRO: Banco de dados não encontrado!")
            return False
    
    try:
        # Tenta fazer o backup em memória como na função original
        bck_conn = sqlite3.connect(":memory:")
        src_conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        src_conn.backup(bck_conn)
        
        # Aqui é onde o erro acontece
        dump_lines = list(bck_conn.iterdump())
        dump_size = len("\n".join(dump_lines))
        
        print(f"✅ Backup bem-sucedido!")
        print(f"   Linhas no dump: {len(dump_lines)}")
        print(f"   Tamanho do dump: {dump_size} bytes")
        
        src_conn.close()
        bck_conn.close()
        return True
        
    except Exception as e:
        print(f"❌ ERRO no backup: {e}")
        return False

if __name__ == "__main__":
    print("Iniciando diagnóstico de foreign keys...")
    
    # Diagnóstico
    fk_ok = diagnosticar_foreign_keys()
    
    # Teste de backup
    backup_ok = testar_backup()
    
    print("\n" + "=" * 60)
    print("RESULTADO FINAL")
    print("=" * 60)
    print(f"Foreign Keys: {'✅ OK' if fk_ok else '❌ PROBLEMAS'}")
    print(f"Backup Test:  {'✅ OK' if backup_ok else '❌ FALHA'}")
    
    if not fk_ok or not backup_ok:
        print("\n🔧 PRÓXIMOS PASSOS:")
        print("1. Execute o script de correção: python corrigir_foreign_keys.py")
        print("2. Re-execute este diagnóstico para validar a correção")
        sys.exit(1)
    else:
        print("\n🎉 Sistema funcionando corretamente!")
        sys.exit(0)