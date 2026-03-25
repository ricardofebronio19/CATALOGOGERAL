#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.insert(0, os.getcwd())

try:
    from core_utils import _normalize_for_search
    
    print("Teste da função _normalize_for_search:")
    print(f"'cabeçote' -> '{_normalize_for_search('cabeçote')}'")
    print(f"'CABEÇOTE' -> '{_normalize_for_search('CABEÇOTE')}'")  
    print(f"'Cabeçote' -> '{_normalize_for_search('Cabeçote')}'")
    print(f"'cabecote' -> '{_normalize_for_search('cabecote')}'")
    print(f"'CABECOTE' -> '{_normalize_for_search('CABECOTE')}'")
    
    # Verifica se são iguais
    norm1 = _normalize_for_search('cabeçote')
    norm2 = _normalize_for_search('CABEÇOTE')
    print(f"\nSão iguais? {norm1 == norm2}")
    print(f"norm1: '{norm1}' (len={len(norm1)})")
    print(f"norm2: '{norm2}' (len={len(norm2)})")
    
except Exception as e:
    print(f"Erro ao importar ou testar: {e}")
    import traceback
    traceback.print_exc()