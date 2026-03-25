#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.insert(0, os.getcwd())

try:
    from app import create_app, db
    from models import Produto
    
    app = create_app()
    
    with app.app_context():
        print("Testando busca com ilike no SQLite:")
        
        # Teste específico para cabeçote
        print("\n=== TESTE 1: Buscar 'cabeçote' (minúsculas) ===")
        resultados1 = Produto.query.filter(Produto.nome.ilike("%cabeçote%")).limit(10).all()
        print(f"Resultados encontrados: {len(resultados1)}")
        for r in resultados1[:5]:
            print(f"  {r.codigo} - {r.nome}")
            
        print("\n=== TESTE 2: Buscar 'CABEÇOTE' (maiúsculas) ===")
        resultados2 = Produto.query.filter(Produto.nome.ilike("%CABEÇOTE%")).limit(10).all()
        print(f"Resultados encontrados: {len(resultados2)}")
        for r in resultados2[:5]:
            print(f"  {r.codigo} - {r.nome}")
            
        print("\n=== TESTE 3: Buscar 'cabecote' (sem acento) ===")
        resultados3 = Produto.query.filter(Produto.nome.ilike("%cabecote%")).limit(10).all()
        print(f"Resultados encontrados: {len(resultados3)}")
        for r in resultados3[:5]:
            print(f"  {r.codigo} - {r.nome}")
            
        # Verificar se os resultados são os mesmos
        ids1 = set(r.id for r in resultados1)
        ids2 = set(r.id for r in resultados2)
        ids3 = set(r.id for r in resultados3)
        
        print(f"\n=== COMPARAÇÃO DE RESULTADOS ===")
        print(f"IDs com 'cabeçote':  {sorted(list(ids1)[:10])}")
        print(f"IDs com 'CABEÇOTE':  {sorted(list(ids2)[:10])}")
        print(f"IDs com 'cabecote':  {sorted(list(ids3)[:10])}")
        
        print(f"\nTodos iguais? {ids1 == ids2 == ids3}")
        print(f"'cabeçote' == 'CABEÇOTE'? {ids1 == ids2}")
        print(f"'cabeçote' == 'cabecote'? {ids1 == ids3}")
        
        # Vamos verificar algumas entradas específicas do banco
        print(f"\n=== DADOS REAIS NO BANCO (amostra) ===")
        amostras = Produto.query.filter(
            db.or_(
                Produto.nome.ilike("%cabeç%"),
                Produto.nome.ilike("%CABEÇ%"),
                Produto.nome.ilike("%Cabeç%")
            )
        ).limit(15).all()
        
        for amostra in amostras:
            print(f"  ID:{amostra.id} | {amostra.codigo} | '{amostra.nome[:60]}...'")
            
except Exception as e:
    print(f"Erro: {e}")
    import traceback
    traceback.print_exc()