"""Debug parsing of a specific CSV row (by codigo) using same logic as import_utils.
Uso: python utils/debug_row_parse.py 18264
"""
import sys
import os
import csv
import re

# garantir import local
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from core_utils import _normalize_for_search

YEAR_PATTERN = r"(\b\d{2,4}(?:/\d{2,4}|/\.\.\.)?\b)"


def build_texto_aplicacoes(row):
    normalized_row = { _normalize_for_search(k.lstrip('\ufeff').strip('"')): v for k,v in row.items() if k }
    def get_value(key):
        return (normalized_row.get(key) or "").strip()
    nome_produto = get_value('nome').strip().upper()
    texto_aplicacoes = ((get_value('aplicacao') or get_value('aplicacoescompletas') or get_value('veiculo') or get_value('aplicacoes')) .strip().upper())
    texto_ano = get_value('ano').strip()
    if texto_ano:
        texto_aplicacoes = f"{texto_aplicacoes} {texto_ano}"
    return nome_produto, texto_aplicacoes


def parse_aplicacoes_text(texto_aplicacoes):
    results = []
    for aplicacao_str in texto_aplicacoes.split('|'):
        aplicacao_str = aplicacao_str.strip()
        if not aplicacao_str:
            continue
        anos_encontrados = re.findall(YEAR_PATTERN, aplicacao_str)
        veiculos_str = re.sub(YEAR_PATTERN, "", aplicacao_str).strip()
        veiculos_potenciais = [v.strip() for v in re.split(r",|\s-\s|\s/\s|\|", veiculos_str) if v.strip()]
        results.append({'orig': aplicacao_str, 'anos': anos_encontrados, 'veiculos': veiculos_potenciais})
    return results


if __name__ == '__main__':
    codigo = sys.argv[1] if len(sys.argv) > 1 else '18264'
    with open('isapa.csv', 'r', encoding='utf-8-sig', errors='ignore') as f:
        reader = csv.DictReader(f)
        found = False
        for row in reader:
            if (row.get('codigo') or '').strip() == str(codigo):
                found = True
                nome, texto = build_texto_aplicacoes(row)
                print('nome:', nome)
                print('texto_aplicacoes raw:', texto)
                parsed = parse_aplicacoes_text(texto)
                for p in parsed:
                    print('->', p)
        if not found:
            print('codigo not found')
