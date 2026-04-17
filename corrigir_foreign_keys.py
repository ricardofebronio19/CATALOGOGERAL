#!/usr/bin/env python3
"""
Script para corrigir problemas de foreign key na tabela compartilhamento_lista
Remove registros órfãos de forma segura
"""

import os
import sys
import sqlite3
import shutil
from datetime import datetime

# Adiciona o diretório atual ao path para importar os modelos
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def fazer_backup_banco():
    """Cria backup do banco antes da correção"""
    db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'catalogo.db')
    if not os.path.exists(db_path):
        db_path = 'catalogo.db'
    
    if not os.path.exists(db_path):
        print("❌ Banco de dados não encontrado!")
        return None, None
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"catalogo_backup_before_fk_fix_{timestamp}.db"
    
    try:
        shutil.copy2(db_path, backup_path)
        print(f"✅ Backup criado: {backup_path}")
        return db_path, backup_path
    except Exception as e:
        print(f"❌ Erro ao criar backup: {e}")
        return None, None

def corrigir_foreign_keys_orphans():
    """Corrige registros órfãos na tabela compartilhamento_lista"""
    
    print("=" * 60)
    print("CORREÇÃO DE FOREIGN KEY ORPHANS")
    print("=" * 60)
    print(f"Iniciado em: {datetime.now()}")
    print()
    
    # Faz backup antes de qualquer modificação
    db_path, backup_path = fazer_backup_banco()
    if not db_path:
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Verifica problemas antes da correção
        cursor.execute("""
            SELECT COUNT(*) FROM compartilhamento_lista 
            WHERE compartilhado_por NOT IN (SELECT id FROM user)
        """)
        problemas_por_count = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT COUNT(*) FROM compartilhamento_lista 
            WHERE compartilhado_com NOT IN (SELECT id FROM user)
        """)
        problemas_com_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM compartilhamento_lista")
        total_before = cursor.fetchone()[0]
        
        print(f"📊 SITUAÇÃO ATUAL:")
        print(f"   Total de compartilhamentos: {total_before}")
        print(f"   Problemas 'compartilhado_por': {problemas_por_count}")
        print(f"   Problemas 'compartilhado_com': {problemas_com_count}")
        print()
        
        if problemas_por_count == 0 and problemas_com_count == 0:
            print("✅ Nenhum problema de FK encontrado!")
            conn.close()
            # Remove backup se não foi necessário
            if backup_path and os.path.exists(backup_path):
                os.remove(backup_path)
                print("🗑️ Backup desnecessário removido")
            return True
        
        # Mostra registros que serão removidos para auditoria
        print("❌ REGISTROS PROBLEMÁTICOS QUE SERÃO REMOVIDOS:")
        
        cursor.execute("""
            SELECT id, lista_id, compartilhado_por, compartilhado_com, criado_em, permissao
            FROM compartilhamento_lista 
            WHERE compartilhado_por NOT IN (SELECT id FROM user)
            OR compartilhado_com NOT IN (SELECT id FROM user)
        """)
        registros_problematicos = cursor.fetchall()
        
        for reg in registros_problematicos:
            print(f"   ID: {reg[0]}, Lista: {reg[1]}, Por: {reg[2]}, Com: {reg[3]}, "
                  f"Data: {reg[4]}, Perm: {reg[5]}")
        
        print(f"\n⚠️  TOTAL DE REGISTROS A SEREM REMOVIDOS: {len(registros_problematicos)}")
        
        # Confirmação de segurança
        resposta = input("\nDeseja continuar com a remoção? (digite 'CONFIRMAR' para prosseguir): ")
        if resposta.strip() != "CONFIRMAR":
            print("❌ Operação cancelada pelo usuário")
            conn.close()
            return False
        
        print("\n🔧 INICIANDO CORREÇÃO...")
        
        # Remove registros problemáticos
        cursor.execute("""
            DELETE FROM compartilhamento_lista 
            WHERE compartilhado_por NOT IN (SELECT id FROM user)
            OR compartilhado_com NOT IN (SELECT id FROM user)
        """)
        
        registros_removidos = cursor.rowcount
        conn.commit()
        
        # Verifica resultado
        cursor.execute("SELECT COUNT(*) FROM compartilhamento_lista")
        total_after = cursor.fetchone()[0]
        
        print(f"✅ CORREÇÃO CONCLUÍDA:")
        print(f"   Registros removidos: {registros_removidos}")
        print(f"   Registros restantes: {total_after}")
        print(f"   Backup salvo em: {backup_path}")
        
        # Testa se foreign keys estão íntegras agora
        cursor.execute("""
            SELECT COUNT(*) FROM compartilhamento_lista 
            WHERE compartilhado_por NOT IN (SELECT id FROM user)
            OR compartilhado_com NOT IN (SELECT id FROM user)
        """)
        problemas_restantes = cursor.fetchone()[0]
        
        if problemas_restantes == 0:
            print("✅ Foreign keys agora estão íntegras!")
            
            # Testa o iterdump
            print("\n🧪 TESTANDO BACKUP (iterdump)...")
            test_conn = sqlite3.connect(":memory:")
            conn.backup(test_conn)
            
            try:
                dump_lines = list(test_conn.iterdump())
                print(f"✅ Teste de backup bem-sucedido! ({len(dump_lines)} linhas)")
                test_conn.close()
                return True
            except Exception as e:
                print(f"❌ Teste de backup ainda falha: {e}")
                test_conn.close()
                return False
        else:
            print(f"❌ Ainda existem {problemas_restantes} problemas restantes!")
            return False
        
    except Exception as e:
        print(f"❌ ERRO durante correção: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def aplicar_constraints_foreign_key():
    """Aplica constraints de foreign key para prevenir futuros problemas"""
    
    print("\n" + "=" * 60)
    print("APLICANDO CONSTRAINTS PREVENTIVAS")
    print("=" * 60)
    
    db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'catalogo.db')
    if not os.path.exists(db_path):
        db_path = 'catalogo.db'
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Verifica se foreign keys estão habilitadas
        cursor.execute("PRAGMA foreign_keys")
        fk_enabled = cursor.fetchone()[0]
        
        print(f"📋 Foreign keys habilitadas: {'✅ Sim' if fk_enabled else '❌ Não'}")
        
        if not fk_enabled:
            print("⚠️  AVISO: Foreign keys não estão habilitadas no SQLite")
            print("   Para máxima segurança, considere habilitar nas configurações da aplicação")
        
        # Verifica integridade do banco
        cursor.execute("PRAGMA integrity_check")
        integrity = cursor.fetchone()[0]
        print(f"🔍 Integridade do banco: {integrity}")
        
        # Verifica especificamente foreign key constraints
        cursor.execute("PRAGMA foreign_key_check")
        fk_violations = cursor.fetchall()
        
        if fk_violations:
            print(f"❌ Violações de FK encontradas: {len(fk_violations)}")
            for violation in fk_violations[:10]:  # Mostra apenas as primeiras 10
                print(f"   {violation}")
        else:
            print("✅ Nenhuma violação de foreign key encontrada!")
        
        return len(fk_violations) == 0
        
    except Exception as e:
        print(f"❌ ERRO ao verificar constraints: {e}")
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    print("Iniciando correção de foreign keys órfãos...")
    
    # Faz a correção
    correcao_ok = corrigir_foreign_keys_orphans()
    
    if correcao_ok:
        # Aplica constraints preventivas
        constraints_ok = aplicar_constraints_foreign_key()
        
        print("\n" + "=" * 60)
        print("RESULTADO FINAL")
        print("=" * 60)
        print(f"Correção:    {'✅ SUCESSO' if correcao_ok else '❌ FALHA'}")
        print(f"Constraints: {'✅ OK' if constraints_ok else '❌ PROBLEMAS'}")
        
        if correcao_ok and constraints_ok:
            print("\n🎉 CORREÇÃO CONCLUÍDA COM SUCESSO!")
            print("   O backup do banco deve funcionar corretamente agora.")
            print("   Execute 'diagnosticar_foreign_keys.py' para confirmar.")
        else:
            print("\n⚠️  CORREÇÃO PARCIAL - verifique os problemas acima")
            
    else:
        print("\n😞 CORREÇÃO FALHOU - verifique os erros acima")
        sys.exit(1)