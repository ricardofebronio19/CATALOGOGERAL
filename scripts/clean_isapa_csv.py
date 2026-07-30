"""Script de limpeza para isapa.csv

Uso:
    python scripts/clean_isapa_csv.py isapa.csv isapa_clean.csv

O script:
- Lê o CSV original tentando ser tolerante com linhas malformadas.
- Garante quatro colunas: codigo, conversoes, nome, aplicacao (veiculo).
- Remove espaços em excesso, normaliza maiúsculas, remove pontos finais.
- Substitui vírgulas internas da coluna de aplicação por pipe '|' para não
  confundir o CSV final.
- Escreve um CSV com cabeçalho: CODIGO,NOME,APLICACAO,CONVERSOES

Feito para uso local antes de rodar o importador.
"""
import csv
import sys
import re

def clean_text(s: str) -> str:
    if s is None:
        return ""
    s = s.strip()
    # Remove múltiplos espaços
    s = re.sub(r"\s+", " ", s)
    # Remove ponto final no final
    s = re.sub(r"\.+$", "", s)
    return s.upper()


def main():
    if len(sys.argv) < 3:
        print("Uso: python scripts/clean_isapa_csv.py <input.csv> <output.csv>")
        sys.exit(1)
    inp = sys.argv[1]
    out = sys.argv[2]

    with open(inp, "r", encoding="utf-8-sig", errors="ignore") as f_in:
        # tentar detectar delimitador simples (esperamos vírgula)
        reader = csv.reader(f_in)
        rows = list(reader)

    cleaned = []
    for row in rows:
        if not row:
            continue
        # Junta colunas extras como parte da última coluna (aplicacao)
        if len(row) >= 4:
            codigo = row[0]
            conversoes = row[1]
            nome = row[2]
            aplicacao = ",".join(row[3:])
        else:
            # Preenche faltantes
            while len(row) < 4:
                row.append("")
            codigo, conversoes, nome, aplicacao = row

        codigo = clean_text(codigo)
        conversoes = clean_text(conversoes)
        nome = clean_text(nome)
        # Substitui vírgulas internas por pipe para separar possíveis múltiplas aplicações
        aplicacao = aplicacao.replace(",", " | ")
        aplicacao = clean_text(aplicacao)

        cleaned.append((codigo, nome, aplicacao, conversoes))

    # Escreve CSV pronto para import
    with open(out, "w", encoding="utf-8", newline="") as f_out:
        writer = csv.writer(f_out)
        # cabeçalho em lowercase e 'aplicacoes' no plural para compatibilidade
        writer.writerow(["codigo", "nome", "aplicacoes", "conversoes"])
        for r in cleaned:
            writer.writerow(r)

    print(f"Arquivo limpo gerado: {out} ({len(cleaned)} linhas)")

if __name__ == "__main__":
    main()
