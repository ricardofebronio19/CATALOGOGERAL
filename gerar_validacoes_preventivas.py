#!/usr/bin/env python3
"""
Sistema de validações preventivas para foreign keys
Adiciona verificações na aplicação para prevenir futuros problemas
"""

import os
import sys
from datetime import datetime

# Adiciona o diretório atual ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def criar_validacoes_models():
    """Adiciona validações aos models para prevenir problemas de FK"""
    
    validacao_code = '''
# === VALIDAÇÕES PREVENTIVAS DE FOREIGN KEY ===
# Adicione este código ao final do models_favoritos.py

from sqlalchemy import event
from sqlalchemy.exc import IntegrityError
import logging

logger = logging.getLogger(__name__)

@event.listens_for(CompartilhamentoLista, 'before_insert')
def validate_compartilhamento_foreign_keys(mapper, connection, target):
    """Valida foreign keys antes de inserir compartilhamento"""
    
    # Verifica se usuários existem
    if target.compartilhado_por:
        result = connection.execute(
            "SELECT COUNT(*) FROM user WHERE id = ?", 
            (target.compartilhado_por,)
        ).fetchone()
        if not result or result[0] == 0:
            logger.error(f"Usuário compartilhado_por não existe: {target.compartilhado_por}")
            raise IntegrityError(
                f"Usuário compartilhado_por {target.compartilhado_por} não existe",
                None, None
            )
    
    if target.compartilhado_com:
        result = connection.execute(
            "SELECT COUNT(*) FROM user WHERE id = ?", 
            (target.compartilhado_com,)
        ).fetchone()
        if not result or result[0] == 0:
            logger.error(f"Usuário compartilhado_com não existe: {target.compartilhado_com}")
            raise IntegrityError(
                f"Usuário compartilhado_com {target.compartilhado_com} não existe",
                None, None
            )


@event.listens_for(CompartilhamentoLista, 'before_update')
def validate_compartilhamento_foreign_keys_update(mapper, connection, target):
    """Valida foreign keys antes de atualizar compartilhamento"""
    validate_compartilhamento_foreign_keys(mapper, connection, target)


def verificar_integridade_foreign_keys():
    """Função utilitária para verificar integridade das FKs"""
    try:
        from app import app, db
        with app.app_context():
            # Verifica compartilhamentos órfãos
            result = db.session.execute("""
                SELECT COUNT(*) FROM compartilhamento_lista 
                WHERE compartilhado_por NOT IN (SELECT id FROM user)
                OR compartilhado_com NOT IN (SELECT id FROM user)
            """).fetchone()
            
            problemas = result[0] if result else 0
            if problemas > 0:
                logger.warning(f"Detectados {problemas} registros com foreign keys órfãos!")
                return False
            return True
            
    except Exception as e:
        logger.error(f"Erro ao verificar integridade de FKs: {e}")
        return False

# === FIM DAS VALIDAÇÕES ===
'''

    print("=" * 60)
    print("VALIDAÇÕES PREVENTIVAS PARA MODELS")
    print("=" * 60)
    print()
    print("📋 CÓDIGO PARA ADICIONAR AO models_favoritos.py:")
    print()
    print(validacao_code)
    print()
    print("🔧 INSTRUÇÕES:")
    print("1. Copie o código acima e cole no final do arquivo models_favoritos.py")
    print("2. Reinicie a aplicação para ativar as validações")
    print("3. As validações impedirão inserções/atualizações com FKs inválidas")
    print()

def criar_funcao_limpeza_routes():
    """Cria função para limpeza periódica de FKs órfãos"""
    
    cleanup_code = '''
# === FUNÇÃO DE LIMPEZA PARA routes.py ou routes_favoritos.py ===

@admin_bp.route("/limpar-foreign-keys")
@login_required
def limpar_foreign_keys_orphans():
    """Remove registros órfãos de compartilhamento_lista"""
    try:
        from models_favoritos import CompartilhamentoLista
        from models import User
        
        # Conta registros problemáticos
        problematicos = CompartilhamentoLista.query.filter(
            ~CompartilhamentoLista.compartilhado_por.in_(
                db.session.query(User.id).subquery()
            ) |
            ~CompartilhamentoLista.compartilhado_com.in_(
                db.session.query(User.id).subquery()
            )
        ).all()
        
        if not problematicos:
            flash("✅ Nenhum registro órfão encontrado!", "success")
            return redirect(url_for("admin.configuracoes"))
        
        # Remove registros órfãos
        for reg in problematicos:
            db.session.delete(reg)
        
        db.session.commit()
        
        flash(f"✅ {len(problematicos)} registros órfãos removidos com sucesso!", "success")
        print(f"[LIMPEZA] Removidos {len(problematicos)} registros órfãos de compartilhamento_lista")
        
    except Exception as e:
        db.session.rollback()
        flash(f"❌ Erro ao limpar registros órfãos: {e}", "danger")
        print(f"[LIMPEZA] Erro: {e}")
    
    return redirect(url_for("admin.configuracoes"))


@admin_bp.route("/verificar-integridade-fk")
@login_required
def verificar_integridade_fk():
    """Verifica integridade das foreign keys sem fazer alterações"""
    try:
        from models_favoritos import CompartilhamentoLista
        from models import User
        
        # Conta total de compartilhamentos
        total = CompartilhamentoLista.query.count()
        
        # Conta registros problemáticos
        problematicos = CompartilhamentoLista.query.filter(
            ~CompartilhamentoListacompartilhado_por.in_(
                db.session.query(User.id).subquery()
            ) |
            ~CompartilhamentoLista.compartilhado_com.in_(
                db.session.query(User.id).subquery()
            )
        ).count()
        
        if problematicos == 0:
            flash(f"✅ Integridade OK! {total} compartilhamentos verificados.", "success")
        else:
            flash(f"⚠️ {problematicos} registros órfãos encontrados de {total} total. "
                  f"Use a função de limpeza para corrigir.", "warning")
        
    except Exception as e:
        flash(f"❌ Erro ao verificar integridade: {e}", "danger")
    
    return redirect(url_for("admin.configuracoes"))

# === FIM DAS FUNÇÕES DE LIMPEZA ===
'''

    print("=" * 60)  
    print("FUNÇÕES DE LIMPEZA PARA ROUTES")
    print("=" * 60)
    print()
    print("📋 CÓDIGO PARA ADICIONAR AO routes.py ou routes_favoritos.py:")
    print()
    print(cleanup_code)
    print()
    print("🔧 INSTRUÇÕES:")
    print("1. Copie o código acima e cole no arquivo routes.py na seção admin")
    print("2. Adicione links na página de configurações para estas funções:")
    print("   - /limpar-foreign-keys (Remove órfãos)")
    print("   - /verificar-integridade-fk (Apenas verifica)")
    print("3. Considere executar a verificação periodicamente")
    print()

def criar_template_configuracoes():
    """Cria template para adicionar botões de limpeza"""
    
    template_code = '''
<!-- === ADICIONAR AO TEMPLATE configuracoes.html === -->

<div class="card mt-4">
    <div class="card-header">
        <h5>🔧 Manutenção do Banco de Dados</h5>
    </div>
    <div class="card-body">
        <div class="row">
            <div class="col-md-6">
                <h6>Verificar Integridade</h6>
                <p class="text-muted">Verifica se existem registros órfãos nas tabelas de relacionamento.</p>
                <a href="{{ url_for('admin.verificar_integridade_fk') }}" 
                   class="btn btn-info btn-sm">
                    <i class="fas fa-search"></i> Verificar Integridade FK
                </a>
            </div>
            <div class="col-md-6">
                <h6>Limpeza Automática</h6>
                <p class="text-muted">Remove registros órfãos que podem causar problemas no backup.</p>
                <a href="{{ url_for('admin.limpar_foreign_keys_orphans') }}" 
                   class="btn btn-warning btn-sm"
                   onclick="return confirm('Deseja remover registros órfãos? Esta ação não pode ser desfeita.')">
                    <i class="fas fa-broom"></i> Limpar Registros Órfãos
                </a>
            </div>
        </div>
    </div>
</div>

<!-- === FIM DO CÓDIGO PARA TEMPLATE === -->
'''

    print("=" * 60)
    print("TEMPLATE PARA PÁGINA DE CONFIGURAÇÕES")
    print("=" * 60)
    print()
    print("📋 HTML PARA ADICIONAR AO configuracoes.html:")
    print()
    print(template_code)
    print()

if __name__ == "__main__":
    print("Gerando código de validações preventivas...")
    print()
    
    criar_validacoes_models()
    criar_funcao_limpeza_routes()
    criar_template_configuracoes()
    
    print("=" * 60)
    print("RESUMO DAS VALIDAÇÕES PREVENTIVAS")
    print("=" * 60)
    print("✅ Validações SQLAlchemy para models_favoritos.py")
    print("✅ Funções de limpeza para routes.py")
    print("✅ Template para interface de administração")
    print()
    print("🎯 PRÓXIMOS PASSOS:")
    print("1. Execute os scripts de diagnóstico e correção primeiro")
    print("2. Implemente as validações preventivas mostradas acima")
    print("3. Teste o backup após implementar as correções")
    print("4. Configure limpeza periódica (opcional)")
    print()
    print("💡 DICA: As validações SQLAlchemy impedirão novos problemas de FK")