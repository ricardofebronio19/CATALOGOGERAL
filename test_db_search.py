#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.insert(0, os.getcwd())

try:
    from app import create_app, db
    from models import Produto
    from core_utils import _apply_db_normalization, _normalize_for_search
    
    app = create_app()
    
    with app.app_context():
        # Testa a função _apply_db_normalization
        print("Testando _apply_db_normalization:")
        
        # Verifica se há produtos no banco
        produtos_count = Produto.query.count()
        print(f"Total de produtos no banco: {produtos_count}")
        
        if produtos_count > 0:
            # Pega alguns produtos para teste
            produtos = Produto.query.limit(5).all()
            print("\nPrimeiros 5 produtos:")
            for p in produtos:
                print(f"ID: {p.id}, Nome: '{p.nome}', Código: '{p.codigo}'")
            
            # Testa busca com normalização
            termo = "cabeçote"
            termo_norm = _normalize_for_search(termo)
            print(f"\nTermo original: '{termo}'")
            print(f"Termo normalizado: '{termo_norm}'")
            
            # Busca usando a função de normalização
            query_norm = Produto.query.filter(
                _apply_db_normalization(Produto.nome).like(f"%{termo_norm}%")
            )
            
            print(f"\nResultados com normalização para '{termo}':")
            resultados_norm = query_norm.limit(10).all()
            for r in resultados_norm:
                print(f"  {r.codigo} - {r.nome}")
            
            # Busca usando ilike tradicional
            query_ilike = Produto.query.filter(
                Produto.nome.ilike(f"%{termo}%")
            )
            
            print(f"\nResultados com ilike para '{termo}':")
            resultados_ilike = query_ilike.limit(10).all()
            for r in resultados_ilike:
                print(f"  {r.codigo} - {r.nome}")
                
        else:
            print("Não há produtos no banco para testar")
            
except Exception as e:
    print(f"Erro: {e}")
    import traceback
    traceback.print_exc()