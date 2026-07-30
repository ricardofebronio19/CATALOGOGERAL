import csv
import re

SRC = r"produtos_1_191.csv"
DST = r"produtos_1_191_import.csv"

def normalize_year(ano_raw: str) -> str:
    if not ano_raw:
        return ""
    s = ano_raw.replace('\u2026', '...')  # normaliza elipse unicode
    s = s.strip()
    # troca múltiplos espaços por um
    s = re.sub(r"\s+", " ", s)
    # remove espaços ao redor de '/'
    s = re.sub(r"\s*/\s*", "/", s)
    # garante que '/...' seja representado por '/...' (3 pontos)
    s = s.replace('/...', '/...')
    return s


def normalize_cell(v: str) -> str:
    if v is None:
        return ""
    v = v.strip()
    v = v.replace('\u2026', '...')
    # colapsa espaços repetidos
    v = re.sub(r"\s+", " ", v)
    return v


def main():
    with open(SRC, 'r', encoding='utf-8-sig', errors='ignore', newline='') as f:
        sniffer = csv.Sniffer()
        sample = f.read(2048)
        f.seek(0)
        try:
            dialect = sniffer.sniff(sample)
        except Exception:
            dialect = csv.excel
        reader = csv.DictReader(f, dialect=dialect)
        # normalize headers
        original_fieldnames = reader.fieldnames or []
        fieldnames = []
        for h in original_fieldnames:
            if h is None:
                continue
            hh = h.strip()
            if hh.lower() == 'observacao':
                hh = 'observacoes'
            fieldnames.append(hh)

        rows = []
        for row in reader:
            new_row = {}
            for k, v in row.items():
                if k is None:
                    continue
                key = k.strip()
                if key.lower() == 'observacao':
                    key = 'observacoes'
                val = normalize_cell(v)
                new_row[key] = val
            # normalize ano field if present
            if 'ano' in new_row:
                new_row['ano'] = normalize_year(new_row['ano'])
            rows.append(new_row)

    # Write output with same (normalized) headers; ensure required headers present
    required = ['codigo','nome','observacoes','aplicacao','ano']
    out_fieldnames = []
    # keep existing normalized headers order, but ensure required are present
    for h in fieldnames:
        if h not in out_fieldnames:
            out_fieldnames.append(h)
    for r in required:
        if r not in out_fieldnames:
            out_fieldnames.append(r)

    with open(DST, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=out_fieldnames, extrasaction='ignore')
        writer.writeheader()
        for r in rows:
            # ensure codigo trimmed
            if 'codigo' in r:
                if not r['codigo'].strip():
                    continue
                r['codigo'] = r['codigo'].strip()
            writer.writerow(r)

    print(f"Arquivo gerado: {DST} (linhas: {len(rows)})")

if __name__ == '__main__':
    main()
