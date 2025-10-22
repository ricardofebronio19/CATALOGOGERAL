import csv
import re

from sqlalchemy import func

from core_utils import _normalize_for_search

from ..app import db
from ..models import Aplicacao, Produto


def _parse_e_salvar_aplicacoes(
    produto_alvo: Produto,
    nome_produto: str,
    texto_aplicacoes: str,
    montadora_geral: str = None,
    grupo: str = None,
    fornecedor: str = None,
    conversoes: str = None,
    observacoes: str = None,
):
    """Interpreta uma string de aplicações e as salva no banco de dados."""
    produto_alvo.nome = nome_produto
    if grupo:
        produto_alvo.grupo = grupo
    if fornecedor:
        produto_alvo.fornecedor = fornecedor
    if conversoes:
        produto_alvo.conversoes = conversoes.upper()
    if observacoes:
        produto_alvo.observacoes = observacoes.upper()

    if produto_alvo.id:
        produto_alvo.aplicacoes.clear()
    db.session.flush()

    if not texto_aplicacoes:
        return

    for aplicacao_str in texto_aplicacoes.split("|"):
        aplicacao_str = aplicacao_str.strip()
        if not aplicacao_str:
            continue

        year_pattern = r"(\b\d{4}(?:/\d{2,4}|/\.{3})?\b)"
        anos_encontrados = re.findall(year_pattern, aplicacao_str)
        veiculos_str = re.sub(year_pattern, "", aplicacao_str).strip()

        montadora = montadora_geral
        if not montadora and "-" in veiculos_str:
            partes = veiculos_str.split("-", 1)
            if len(partes[0]) < 15 and partes[0].isupper():
                montadora = partes[0].strip()
                veiculos_str = partes[1].strip()

        veiculos_potenciais = [
            v.strip() for v in re.split(r"[, ]+", veiculos_str) if v.strip()
        ]

        for veiculo_nome in veiculos_potenciais:
            if montadora and veiculo_nome.startswith(montadora):
                veiculo_nome = veiculo_nome[len(montadora):].lstrip(" -")

            ano_str = " / ".join(anos_encontrados)
            nova_aplicacao = Aplicacao(
                veiculo=veiculo_nome,
                ano=ano_str.strip(),
                montadora=montadora,
                produto=produto_alvo,
            )
            db.session.add(nova_aplicacao)


def importar_csv_logic(app, filepath):
    """Lógica principal para importar produtos de um arquivo CSV."""
    with app.app_context():
        produtos_adicionados = 0
        produtos_atualizados = 0
        print(f"Iniciando importação de '{filepath}'...")
        try:
            with open(filepath, "r", encoding="utf-8-sig", errors="ignore") as f:
                # Detecta delimitador
                sniffer = csv.Sniffer()
                dialect = sniffer.sniff(f.read(1024))
                f.seek(0)
                reader = csv.DictReader(f, dialect=dialect)

                for row in reader:
                    normalized_row = {
                        _normalize_for_search(k.lstrip("\ufeff").strip('"')): v
                        for k, v in row.items()
                        if k
                    }

                    def get_value(key):
                        return (normalized_row.get(key) or "").strip()

                    codigo = get_value("codigo").strip()
                    if not codigo:
                        continue

                    nome_produto = get_value("nome").strip().upper()
                    texto_aplicacoes = (
                        (
                            get_value("aplicacao")
                            or get_value("aplicacoescompletas")
                            or get_value("veiculo")
                            or get_value("aplicacoes")
                        )
                        .strip()
                        .upper()
                    )
                    texto_ano = get_value("ano").strip()
                    if texto_ano:
                        texto_aplicacoes = f"{texto_aplicacoes} {texto_ano}"

                    grupo = get_value("grupo").strip().upper()
                    fornecedor = (
                        (
                            get_value("fornecedor")
                            or get_value("fabricante")
                            or get_value("marca")
                        )
                        .strip()
                        .upper()
                    )
                    montadora_geral = get_value("montadorasaplicacoes").strip().upper()
                    conversoes = (
                        get_value("conversoes")
                        or get_value("nconversoes")
                        or get_value("conversao")
                    ).strip()
                    observacoes = (get_value("observacoes") or get_value("obs")).strip()

                    produto_existente = Produto.query.filter(
                        func.upper(Produto.codigo) == codigo.upper()
                    ).first()
                    produto_alvo = produto_existente or Produto(codigo=codigo)
                    if not produto_existente:
                        db.session.add(produto_alvo)
                        produtos_adicionados += 1
                    else:
                        produtos_atualizados += 1

                    _parse_e_salvar_aplicacoes(
                        produto_alvo,
                        nome_produto,
                        texto_aplicacoes,
                        montadora_geral,
                        grupo,
                        fornecedor,
                        conversoes,
                        observacoes,
                    )

                db.session.commit()
                print(
                    "Importação concluída! "
                    + str(produtos_adicionados)
                    + " produtos adicionados, "
                    + str(produtos_atualizados)
                    + " atualizados."
                )
        except Exception as e:
            db.session.rollback()
            print(f"Ocorreu um erro inesperado durante a importação: {e}")
