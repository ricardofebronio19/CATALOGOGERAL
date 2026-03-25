#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.insert(0, os.getcwd())

from app import create_app, db
from models import Produto, Aplicacao, ImagemProduto, SugestaoIgnorada

def analisar_aplicacoes_orfas():
    """Analisa o banco de dados para encontrar aplicações órfãs."""
    
    app = create_app()
    
    with app.app_context():
        print("=== ANÁLISE DE APLICAÇÕES ÓRFÃS ===\n")
        
        # 1. Contar totais
        total_produtos = Produto.query.count()
        total_aplicacoes = Aplicacao.query.count()
        
        print(f"Total de produtos no banco: {total_produtos}")
        print(f"Total de aplicações no banco: {total_aplicacoes}")
        
        # 2. Encontrar aplicações com produto_id que não existe mais
        aplicacoes_orfas = db.session.query(Aplicacao).filter(
            ~Aplicacao.produto_id.in_(
                db.session.query(Produto.id)
            )
        ).all()
        
        print(f"\nAplicações órfãs encontradas: {len(aplicacoes_orfas)}")
        
        if aplicacoes_orfas:
            print("\nDetalhes das aplicações órfãs:")
            print("-" * 80)
            print(f"{'ID':<8} {'Produto ID':<12} {'Montadora':<15} {'Veículo':<20} {'Ano':<10} {'Motor':<15}")
            print("-" * 80)
            
            for app in aplicacoes_orfas[:20]:  # Mostra apenas as primeiras 20
                montadora = (app.montadora or "")[:14]
                veiculo = (app.veiculo or "")[:19]
                ano = (app.ano or "")[:9]
                motor = (app.motor or "")[:14]
                print(f"{app.id:<8} {app.produto_id:<12} {montadora:<15} {veiculo:<20} {ano:<10} {motor:<15}")
            
            if len(aplicacoes_orfas) > 20:
                print(f"... e mais {len(aplicacoes_orfas) - 20} aplicações órfãs")
        
        # 3. Verificar outras tabelas com referências órfãs
        print(f"\n=== OUTRAS REFERÊNCIAS ÓRFÃS ===")
        
        # Imagens órfãs
        imagens_orfas = db.session.query(ImagemProduto).filter(
            ~ImagemProduto.produto_id.in_(
                db.session.query(Produto.id)
            )
        ).count()
        print(f"Imagens órfãs: {imagens_orfas}")
        
        # Sugestões órfãs
        sugestoes_orfas_produto = db.session.query(SugestaoIgnorada).filter(
            ~SugestaoIgnorada.produto_id.in_(
                db.session.query(Produto.id)
            )
        ).count()
        
        sugestoes_orfas_sugestao = db.session.query(SugestaoIgnorada).filter(
            ~SugestaoIgnorada.sugestao_id.in_(
                db.session.query(Produto.id)
            )
        ).count()
        
        print(f"Sugestões com produto_id órfão: {sugestoes_orfas_produto}")
        print(f"Sugestões com sugestao_id órfão: {sugestoes_orfas_sugestao}")
        
        # 4. Verificar produtos sem aplicações
        produtos_sem_aplicacoes = db.session.query(Produto).filter(
            ~Produto.id.in_(
                db.session.query(Aplicacao.produto_id).distinct()
            )
        ).count()
        print(f"Produtos sem aplicações: {produtos_sem_aplicacoes}")
        
        return len(aplicacoes_orfas)


def limpar_aplicacoes_orfas(confirmar=False):
    """Remove aplicações órfãs do banco de dados."""
    
    app = create_app()
    
    with app.app_context():
        # Encontrar aplicações órfãs
        aplicacoes_orfas = db.session.query(Aplicacao).filter(
            ~Aplicacao.produto_id.in_(
                db.session.query(Produto.id)
            )
        ).all()
        
        if not aplicacoes_orfas:
            print("✅ Nenhuma aplicação órfã encontrada!")
            return 0
        
        print(f"⚠️  Encontradas {len(aplicacoes_orfas)} aplicações órfãs para exclusão")
        
        if not confirmar:
            print("\n⚠️  AVISO: Esta operação é IRREVERSÍVEL!")
            print("Para confirmar a exclusão, execute novamente com confirmar=True")
            return 0
        
        try:
            # Excluir aplicações órfãs
            ids_para_excluir = [app.id for app in aplicacoes_orfas]
            
            db.session.query(Aplicacao).filter(
                Aplicacao.id.in_(ids_para_excluir)
            ).delete(synchronize_session=False)
            
            db.session.commit()
            
            print(f"✅ {len(aplicacoes_orfas)} aplicações órfãs foram excluídas com sucesso!")
            return len(aplicacoes_orfas)
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Erro ao excluir aplicações órfãs: {e}")
            return 0


def limpar_todas_referencias_orfas(confirmar=False):
    """Remove todas as referências órfãs do banco de dados."""
    
    app = create_app()
    
    with app.app_context():
        total_removidos = 0
        
        if not confirmar:
            print("\n⚠️  AVISO: Esta operação remove TODAS as referências órfãs e é IRREVERSÍVEL!")
            print("Para confirmar, execute novamente com confirmar=True")
            return 0
        
        try:
            # 1. Aplicações órfãs
            aplicacoes_orfas = db.session.query(Aplicacao).filter(
                ~Aplicacao.produto_id.in_(db.session.query(Produto.id))
            ).count()
            
            if aplicacoes_orfas > 0:
                db.session.query(Aplicacao).filter(
                    ~Aplicacao.produto_id.in_(db.session.query(Produto.id))
                ).delete(synchronize_session=False)
                total_removidos += aplicacoes_orfas
                print(f"✅ Removidas {aplicacoes_orfas} aplicações órfãs")
            
            # 2. Imagens órfãs
            imagens_orfas = db.session.query(ImagemProduto).filter(
                ~ImagemProduto.produto_id.in_(db.session.query(Produto.id))
            ).count()
            
            if imagens_orfas > 0:
                db.session.query(ImagemProduto).filter(
                    ~ImagemProduto.produto_id.in_(db.session.query(Produto.id))
                ).delete(synchronize_session=False)
                total_removidos += imagens_orfas
                print(f"✅ Removidas {imagens_orfas} imagens órfãs")
            
            # 3. Sugestões órfãs
            sugestoes_orfas = db.session.query(SugestaoIgnorada).filter(
                db.or_(
                    ~SugestaoIgnorada.produto_id.in_(db.session.query(Produto.id)),
                    ~SugestaoIgnorada.sugestao_id.in_(db.session.query(Produto.id))
                )
            ).count()
            
            if sugestoes_orfas > 0:
                db.session.query(SugestaoIgnorada).filter(
                    db.or_(
                        ~SugestaoIgnorada.produto_id.in_(db.session.query(Produto.id)),
                        ~SugestaoIgnorada.sugestao_id.in_(db.session.query(Produto.id))
                    )
                ).delete(synchronize_session=False)
                total_removidos += sugestoes_orfas
                print(f"✅ Removidas {sugestoes_orfas} sugestões órfãs")
            
            db.session.commit()
            print(f"\n🎉 Limpeza concluída! Total de registros removidos: {total_removidos}")
            return total_removidos
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Erro durante a limpeza: {e}")
            return 0


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Analisar e limpar aplicações órfãs")
    parser.add_argument("--analisar", action="store_true", help="Apenas analisar (não excluir)")
    parser.add_argument("--limpar-aplicacoes", action="store_true", help="Limpar apenas aplicações órfãs")
    parser.add_argument("--limpar-tudo", action="store_true", help="Limpar todas as referências órfãs")
    parser.add_argument("--confirmar", action="store_true", help="Confirmar a exclusão")
    
    args = parser.parse_args()
    
    if args.analisar or not any([args.limpar_aplicacoes, args.limpar_tudo]):
        # Por padrão, apenas analisa
        aplicacoes_orfas = analisar_aplicacoes_orfas()
        
        if aplicacoes_orfas > 0:
            print(f"\n💡 Para limpar as aplicações órfãs, execute:")
            print(f"   python {sys.argv[0]} --limpar-aplicacoes --confirmar")
            print(f"\n💡 Para limpar todas as referências órfãs, execute:")
            print(f"   python {sys.argv[0]} --limpar-tudo --confirmar")
    
    elif args.limpar_aplicacoes:
        limpar_aplicacoes_orfas(confirmar=args.confirmar)
    
    elif args.limpar_tudo:
        limpar_todas_referencias_orfas(confirmar=args.confirmar)