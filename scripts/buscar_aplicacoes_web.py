"""
buscar_aplicacoes_web.py
------------------------
Busca aplicações (veículos compatíveis) para produtos do catálogo
consultando a internet via Google e tentando sites de referência de peças.

Uso:
    # Busca para todos os produtos SEM aplicação cadastrada:
    python scripts/buscar_aplicacoes_web.py

    # Busca para um produto específico pelo ID:
    python scripts/buscar_aplicacoes_web.py --id 42

    # Busca para um código + fornecedor direto (sem banco):
    python scripts/buscar_aplicacoes_web.py --codigo 24349 --fornecedor frontier

    # Limita quantos produtos processar (útil para testes):
    python scripts/buscar_aplicacoes_web.py --limite 10

    # Salva resultados em CSV para revisão manual:
    python scripts/buscar_aplicacoes_web.py --saida resultados_aplicacoes.csv

    # Importa automaticamente para o banco após confirmação:
    python scripts/buscar_aplicacoes_web.py --importar

Dependências:
    pip install requests beautifulsoup4 lxml

ATENÇÃO: Este script faz buscas na internet. Use com responsabilidade —
         respeita delays entre requisições para não sobrecarregar servidores.
"""

import argparse
import csv
import os
import re
import sys
import time
import unicodedata

# ── path setup ──────────────────────────────────────────────────────────────
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# ── dependências opcionais ───────────────────────────────────────────────────
try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("❌  Dependências ausentes. Execute:")
    print("    pip install requests beautifulsoup4 lxml")
    sys.exit(1)

# ── configurações ────────────────────────────────────────────────────────────
DELAY_ENTRE_BUSCAS = 2.5   # segundos entre cada requisição (respeito aos servidores)
TIMEOUT_REQUISICAO = 12    # segundos de timeout por requisição
MAX_RESULTADOS_POR_PRODUTO = 8  # máximo de aplicações a extrair por produto

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "pt-BR,pt;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

# Montadoras conhecidas para ajudar na extração do texto
MONTADORAS_CONHECIDAS = [
    "volkswagen", "vw", "fiat", "chevrolet", "gm", "ford", "renault",
    "peugeot", "citroen", "toyota", "honda", "hyundai", "kia", "nissan",
    "mitsubishi", "jeep", "dodge", "chrysler", "bmw", "mercedes", "audi",
    "volvo", "land rover", "subaru", "mazda", "suzuki", "seat", "skoda",
    "frontier", "ram", "troller",
]

# ── normalização de texto ────────────────────────────────────────────────────
def normalizar(texto: str) -> str:
    """Remove acentos e converte para minúsculas."""
    nfkd = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in nfkd if not unicodedata.combining(c)).lower().strip()


# ── extração de aplicações do texto ─────────────────────────────────────────
# Padrão: captura "Clio 2001/2005", "Gol 1.0 2003", "Palio Weekend 1.6 2000/..."
RE_APLICACAO = re.compile(
    r"""
    (?P<veiculo>[A-Za-zÀ-ú][\w\sÀ-ú\-\.]{2,40}?)   # nome do veículo
    \s+
    (?P<motor>(?:\d[\.\d]*\s*(?:16v|8v|turbo|tdi|flex|vvt|vtec)?)?)?  # motor (opcional)
    \s*
    (?P<ano>\d{4}(?:[\/\-\.]\d{2,4})?(?:[\/\-\.]\.\.\.)?)             # ano ou intervalo
    """,
    re.VERBOSE | re.IGNORECASE,
)

RE_ANO_UNICO = re.compile(r"\b(19|20)\d{2}\b")


def extrair_aplicacoes_do_texto(texto: str) -> list[dict]:
    """
    Tenta extrair pares (veículo, ano, motor) de um bloco de texto livre.
    Retorna lista de dicts com keys: veiculo, ano, motor, montadora.
    """
    resultados = []
    visto = set()

    for m in RE_APLICACAO.finditer(texto):
        veiculo_raw = m.group("veiculo").strip(" .,;:-")
        motor_raw   = (m.group("motor") or "").strip()
        ano_raw     = m.group("ano").strip()

        if len(veiculo_raw) < 2 or not RE_ANO_UNICO.search(ano_raw):
            continue

        # Detecta montadora pelo início do nome do veículo
        montadora = ""
        veiculo_norm = normalizar(veiculo_raw)
        for marca in MONTADORAS_CONHECIDAS:
            if veiculo_norm.startswith(marca):
                montadora = marca.title()
                # Remove o nome da montadora do campo veiculo
                veiculo_raw = veiculo_raw[len(marca):].strip(" .,;:-")
                break

        chave = (normalizar(veiculo_raw), ano_raw)
        if chave in visto:
            continue
        visto.add(chave)

        resultados.append({
            "montadora": montadora,
            "veiculo":   veiculo_raw,
            "motor":     motor_raw,
            "ano":       ano_raw,
        })

        if len(resultados) >= MAX_RESULTADOS_POR_PRODUTO:
            break

    return resultados


# ── estratégias de busca ─────────────────────────────────────────────────────
def buscar_google(codigo: str, fornecedor: str) -> str:
    """
    Faz uma busca no Google e retorna o texto dos snippets.
    Usa a URL de busca simples — não requer API key.
    """
    query = f"{fornecedor} {codigo} aplicação veículo compatível"
    url = f"https://www.google.com/search?q={requests.utils.quote(query)}&hl=pt-BR&num=5"

    try:
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT_REQUISICAO)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")

        # Coleta todos os snippets de resultado
        blocos = soup.select("div.BNeawe, div.VwiC3b, span.aCOpRe, div.IsZvec")
        textos = [b.get_text(" ", strip=True) for b in blocos]
        return " | ".join(textos)
    except Exception as exc:
        print(f"    ⚠ Google: {exc}")
        return ""


def buscar_mecanicaonline(codigo: str, fornecedor: str) -> str:
    """Tenta buscar no mecanicaonline.com.br."""
    url = f"https://www.mecanicaonline.com.br/catalogo/?q={codigo}+{fornecedor}"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT_REQUISICAO)
        soup = BeautifulSoup(resp.text, "lxml")
        return soup.get_text(" ", strip=True)
    except Exception:
        return ""


def buscar_pecasauto(codigo: str, fornecedor: str) -> str:
    """Tenta buscar no pecasauto.com.br."""
    url = f"https://www.pecasauto.com.br/search?q={codigo}+{fornecedor}"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT_REQUISICAO)
        soup = BeautifulSoup(resp.text, "lxml")
        return soup.get_text(" ", strip=True)
    except Exception:
        return ""


def pesquisar_aplicacoes(codigo: str, fornecedor: str) -> list[dict]:
    """
    Orquestra todas as estratégias de busca para um produto.
    Retorna lista de aplicações encontradas.
    """
    print(f"  🔎  Buscando: {fornecedor} {codigo}")
    textos = []

    # 1. Google (mais abrangente)
    t = buscar_google(codigo, fornecedor)
    if t:
        textos.append(t)
    time.sleep(DELAY_ENTRE_BUSCAS)

    # 2. Sites especializados (sem delay extra — já respeitamos o Google)
    t2 = buscar_mecanicaonline(codigo, fornecedor)
    if t2:
        textos.append(t2)

    t3 = buscar_pecasauto(codigo, fornecedor)
    if t3:
        textos.append(t3)

    texto_total = " ".join(textos)
    aplicacoes = extrair_aplicacoes_do_texto(texto_total)

    print(f"  {'✅' if aplicacoes else '⚠ '}  {len(aplicacoes)} aplicações encontradas")
    return aplicacoes


# ── banco de dados ───────────────────────────────────────────────────────────
def obter_produtos_sem_aplicacao(limite: int | None = None):
    """Retorna produtos do banco que não possuem nenhuma aplicação."""
    import app as flask_app
    from models import Produto

    with flask_app.app.app_context():
        q = Produto.query.filter(~Produto.aplicacoes.any()).order_by(Produto.id)
        if limite:
            q = q.limit(limite)
        # Retorna dados simples para usar fora do contexto
        return [
            {"id": p.id, "codigo": p.codigo, "fornecedor": p.fornecedor or "", "nome": p.nome}
            for p in q.all()
        ]


def obter_produto_por_id(produto_id: int):
    import app as flask_app
    from models import Produto

    with flask_app.app.app_context():
        p = Produto.query.get(produto_id)
        if not p:
            return None
        return {"id": p.id, "codigo": p.codigo, "fornecedor": p.fornecedor or "", "nome": p.nome}


def importar_aplicacoes_para_banco(produto_id: int, aplicacoes: list[dict]):
    """Insere as aplicações encontradas no banco para o produto informado."""
    import app as flask_app
    from models import Aplicacao
    from app import db

    with flask_app.app.app_context():
        for ap in aplicacoes:
            nova = Aplicacao(
                produto_id=produto_id,
                montadora=ap.get("montadora") or None,
                veiculo=ap.get("veiculo") or None,
                ano=ap.get("ano") or None,
                motor=ap.get("motor") or None,
            )
            db.session.add(nova)
        db.session.commit()
        print(f"    💾  {len(aplicacoes)} aplicações importadas para produto ID {produto_id}")


# ── saída CSV ────────────────────────────────────────────────────────────────
def salvar_csv(linhas: list[dict], caminho: str):
    campos = ["produto_id", "codigo", "fornecedor", "nome",
              "montadora", "veiculo", "motor", "ano"]
    with open(caminho, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=campos, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(linhas)
    print(f"\n📄  Resultados salvos em: {caminho}")


# ── main ─────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="Busca aplicações de peças na internet e opcionalmente importa para o banco."
    )
    parser.add_argument("--id",         type=int,   help="ID do produto no banco")
    parser.add_argument("--codigo",     type=str,   help="Código do produto (sem banco)")
    parser.add_argument("--fornecedor", type=str,   help="Fornecedor do produto (sem banco)")
    parser.add_argument("--limite",     type=int,   help="Nº máximo de produtos a processar")
    parser.add_argument("--saida",      type=str,   default="aplicacoes_encontradas.csv",
                        help="Arquivo CSV de saída (padrão: aplicacoes_encontradas.csv)")
    parser.add_argument("--importar",   action="store_true",
                        help="Importar resultados para o banco após confirmação")
    args = parser.parse_args()

    # ── modo direto (sem banco) ──────────────────────────────────────────────
    if args.codigo and args.fornecedor:
        aplicacoes = pesquisar_aplicacoes(args.codigo.strip(), args.fornecedor.strip())
        if aplicacoes:
            print("\nAplicações encontradas:")
            for ap in aplicacoes:
                print(f"  {ap['montadora']:15} {ap['veiculo']:20} {ap['motor']:10} {ap['ano']}")
        else:
            print("Nenhuma aplicação encontrada.")
        return

    # ── modo banco de dados ──────────────────────────────────────────────────
    if args.id:
        produto = obter_produto_por_id(args.id)
        if not produto:
            print(f"❌  Produto ID {args.id} não encontrado.")
            sys.exit(1)
        produtos = [produto]
    else:
        print("🔍  Carregando produtos sem aplicação do banco...")
        produtos = obter_produtos_sem_aplicacao(args.limite)
        print(f"    {len(produtos)} produtos encontrados.\n")

    if not produtos:
        print("✅  Nenhum produto sem aplicação. Nada a fazer.")
        return

    todas_linhas_csv = []
    resultados_para_importar = []  # lista de (produto_id, aplicacoes)

    for i, prod in enumerate(produtos, 1):
        print(f"[{i}/{len(produtos)}] {prod['nome']} — {prod['fornecedor']} {prod['codigo']}")
        aplicacoes = pesquisar_aplicacoes(prod["codigo"], prod["fornecedor"])

        for ap in aplicacoes:
            todas_linhas_csv.append({
                "produto_id": prod["id"],
                "codigo":     prod["codigo"],
                "fornecedor": prod["fornecedor"],
                "nome":       prod["nome"],
                **ap,
            })

        if aplicacoes:
            resultados_para_importar.append((prod["id"], aplicacoes))

        # Delay adicional entre produtos para não sobrecarregar
        if i < len(produtos):
            time.sleep(DELAY_ENTRE_BUSCAS)

    # ── salva CSV ────────────────────────────────────────────────────────────
    if todas_linhas_csv:
        salvar_csv(todas_linhas_csv, args.saida)
        print(f"\n📊  Total: {len(todas_linhas_csv)} aplicações para {len(resultados_para_importar)} produtos")
    else:
        print("\n⚠  Nenhuma aplicação foi encontrada para os produtos pesquisados.")
        print("   Dicas:")
        print("   - Verifique se o código e fornecedor estão corretos")
        print("   - Tente nomes alternativos do fornecedor")
        print("   - A informação pode não estar disponível online")
        return

    # ── importação opcional ──────────────────────────────────────────────────
    if args.importar:
        print(f"\n⚠  Prestes a importar {len(todas_linhas_csv)} aplicações para o banco.")
        resposta = input("Confirma importação? (s/N): ").strip().lower()
        if resposta == "s":
            for produto_id, aplicacoes in resultados_para_importar:
                importar_aplicacoes_para_banco(produto_id, aplicacoes)
            print("✅  Importação concluída!")
        else:
            print("❌  Importação cancelada. O CSV foi mantido para revisão manual.")
    else:
        print(f"\n💡  Para importar, revise o CSV '{args.saida}' e execute com --importar")


if __name__ == "__main__":
    main()
