!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para validar o arquivo CSV processado antes da importação.
Verifica se as colunas necessárias estão presentes e se os dados estão formatados corretamente.
"""

import csv
import re
from pathlib import Path


def validate_csv_for_import(filepath: str) -> bool:
    """Valida se o CSV está pronto para importação no catálogo."""
    
    print(f"Validando arquivo: {filepath}")
    print("=" * 50)
    
    # Colunas esperadas pelo sistema de importação
    expected_columns = {
        'codigo': 'Código do produto (obrigatório)',
        'nome': 'Nome do produto (obrigatório)', 
        'grupo': 'Grupo/categoria (opcional)',
        'fornecedor': 'Fabricante/marca (opcional)',
        'aplicacao': 'Aplicações/veículos (opcional)',
        'medidas': 'Medidas técnicas (opcional)',
        'observacoes': 'Observações (opcional)',
        'conversoes': 'Códigos de conversão (opcional)'
    }
    
    errors = []
    warnings = []
    stats = {
        'total_rows': 0,
        'valid_rows': 0,
        'empty_codigo': 0,
        'empty_nome': 0,
        'with_fornecedor': 0,
        'with_aplicacao': 0,
        'with_grupo': 0
    }
    
    try:
        with open(filepath, 'r', encoding='utf-8', newline='') as f:
            reader = csv.DictReader(f)
            
            # Verifica cabeçalhos
            fieldnames = reader.fieldnames or []
            print(f"Colunas encontradas: {fieldnames}")
            print()
            
            # Verifica se as colunas obrigatórias existem
            missing_required = []
            for col in ['codigo', 'nome']:
                if col not in fieldnames:
                    missing_required.append(col)
            
            if missing_required:
                errors.append(f"Colunas obrigatórias faltando: {missing_required}")
            
            # Verifica colunas extras
            extra_columns = set(fieldnames) - set(expected_columns.keys())
            if extra_columns:
                warnings.append(f"Colunas extras encontradas (serão ignoradas): {extra_columns}")
            
            # Valida dados linha por linha
            for row_num, row in enumerate(reader, start=2):  # Start=2 porque linha 1 é cabeçalho
                stats['total_rows'] += 1
                
                codigo = (row.get('codigo') or '').strip()
                nome = (row.get('nome') or '').strip()
                grupo = (row.get('grupo') or '').strip()
                fornecedor = (row.get('fornecedor') or '').strip()
                aplicacao = (row.get('aplicacao') or '').strip()
                
                # Verifica campos obrigatórios
                if not codigo:
                    stats['empty_codigo'] += 1
                    errors.append(f"Linha {row_num}: Código vazio")
                
                if not nome:
                    stats['empty_nome'] += 1
                    warnings.append(f"Linha {row_num}: Nome vazio (código: {codigo})")
                
                # Atualiza estatísticas
                if codigo and nome:
                    stats['valid_rows'] += 1
                
                if fornecedor:
                    stats['with_fornecedor'] += 1
                
                if aplicacao:
                    stats['with_aplicacao'] += 1
                    
                if grupo:
                    stats['with_grupo'] += 1
                
                # Validações de formato
                if codigo and len(codigo) > 50:
                    warnings.append(f"Linha {row_num}: Código muito longo ({len(codigo)} chars): {codigo[:50]}...")
                
                if nome and len(nome) > 200:
                    warnings.append(f"Linha {row_num}: Nome muito longo ({len(nome)} chars)")
                
                # Para por na linha 1000 para não fazer o log muito longo
                if row_num > 1000 and errors:
                    break
        
    except Exception as e:
        errors.append(f"Erro ao ler arquivo: {e}")
        return False
    
    # Relatório de validação
    print("RESULTADOS DA VALIDAÇÃO:")
    print("=" * 25)
    print(f"✅ Total de linhas: {stats['total_rows']}")
    print(f"✅ Linhas válidas: {stats['valid_rows']}")
    print(f"✅ Com fornecedor: {stats['with_fornecedor']}")
    print(f"✅ Com aplicação: {stats['with_aplicacao']}")
    print(f"✅ Com grupo: {stats['with_grupo']}")
    print()
    
    if errors:
        print("❌ ERROS ENCONTRADOS:")
        for error in errors[:10]:  # Mostra apenas os primeiros 10 erros
            print(f"  • {error}")
        if len(errors) > 10:
            print(f"  ... e mais {len(errors) - 10} erros")
        print()
    
    if warnings:
        print("⚠️ AVISOS:")
        for warning in warnings[:10]:  # Mostra apenas os primeiros 10 avisos
            print(f"  • {warning}")
        if len(warnings) > 10:
            print(f"  ... e mais {len(warnings) - 10} avisos")
        print()
    
    # Verifica se está pronto para importação
    is_valid = len(errors) == 0 and stats['valid_rows'] > 0
    
    if is_valid:
        print("✅ ARQUIVO VÁLIDO PARA IMPORTAÇÃO!")
        print(f"📊 {stats['valid_rows']} produtos serão importados")
        print()
        print("Para importar, execute:")
        print(f"python run.py import-csv \"{filepath}\"")
    else:
        print("❌ ARQUIVO NÃO ESTÁ PRONTO PARA IMPORTAÇÃO")
        print("Corrija os erros listados acima antes de importar.")
    
    return is_valid


def main():
    """Função principal."""
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    csv_file = project_root / "ISAPA_import_ready.csv"
    
    if not csv_file.exists():
        print(f"❌ Arquivo não encontrado: {csv_file}")
        print("Execute primeiro o script prepare_isapa_csv.py")
        return
    
    print("=== Validação do arquivo CSV para importação ===")
    print()
    
    validate_csv_for_import(str(csv_file))


if __name__ == "__main__":
    main()