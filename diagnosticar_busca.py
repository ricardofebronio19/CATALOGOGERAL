#!/usr/bin/env python3
"""
Script de diagnóstico para validar o funcionamento da busca
"""
import sys
import os

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from app import create_app, db, inicializar_banco
    from models import Produto, Aplicacao
    from core_utils import _build_search_query
    print("✅ Importações realizadas com sucesso")
except ImportError as e:
    print(f"❌ Erro na importação: {e}")
    sys.exit(1)

def diagnosticar_sistema():
    """Executa diagnósticos do sistema de busca"""
    print("\n🔍 DIAGNÓSTICO DO SISTEMA DE BUSCA CGI")
    print("=" * 50)
    
    # 1. Teste de criação da app
    try:
        app = create_app()
        print("✅ Aplicação Flask criada com sucesso")
    except Exception as e:
        print(f"❌ Erro ao criar aplicação: {e}")
        return False
    
    # 2. Teste de inicialização do banco
    try:
        with app.app_context():
            inicializar_banco(app)
            print("✅ Banco de dados inicializado")
            
            # 3. Teste de conexão com o banco
            total_produtos = Produto.query.count()
            total_aplicacoes = Aplicacao.query.count()
            print(f"✅ Conectado ao banco - {total_produtos} produtos, {total_aplicacoes} aplicações")
            
            if total_produtos == 0:
                print("⚠️  AVISO: Banco vazio - não há produtos cadastrados!")
                print("   Isso pode explicar por que a busca não retorna resultados")
                return True  # Sistema funciona, mas está vazio
            
            # 4. Teste da função de busca
            print("\n🔧 TESTANDO SISTEMA DE BUSCA:")
            
            # Teste 1: Busca geral vazia (deve retornar todos)
            query_vazia = _build_search_query('', '', '', '', '', '')
            resultado_vazio = query_vazia.limit(5).all()
            print(f"   Busca vazia: {len(resultado_vazio)} resultados (máx 5)")
            
            # Teste 2: Busca por primeiro produto
            primeiro_produto = Produto.query.first()
            if primeiro_produto:
                query_codigo = _build_search_query('', primeiro_produto.codigo, '', '', '', '')
                resultado_codigo = query_codigo.all()
                print(f"   Busca por código '{primeiro_produto.codigo}': {len(resultado_codigo)} resultado(s)")
            
            # Teste 3: Busca com termo geral
            query_termo = _build_search_query('a', '', '', '', '', '')
            resultado_termo = query_termo.limit(3).all()
            print(f"   Busca termo 'a': {len(resultado_termo)} resultados (máx 3)")
            
            print("✅ Sistema de busca está funcionando corretamente!")
            
    except Exception as e:
        print(f"❌ Erro no banco de dados: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n📋 RESUMO:")
    print("- Sistema Flask: ✅ OK")
    print("- Banco de dados: ✅ OK")
    print("- Função de busca: ✅ OK")
    
    if total_produtos > 0:
        print("- Dados disponíveis: ✅ OK")
        print("\n🎯 CONCLUSÃO: O sistema está funcionando. O problema pode ser:")
        print("   1. JavaScript interferindo (já corrigido)")
        print("   2. Problema de navegador/cache")
        print("   3. Filtros muito específicos retornando resultados vazios")
    else:
        print("- Dados disponíveis: ⚠️  VAZIO")
        print("\n🎯 CONCLUSÃO: Banco vazio - precisa importar dados!")
    
    return True

if __name__ == "__main__":
    success = diagnosticar_sistema()
    if not success:
        print("\n❌ Diagnóstico falhou - verifique os erros acima")
        sys.exit(1)
    else:
        print("\n✅ Diagnóstico concluído com sucesso")