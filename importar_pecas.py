import csv
import json
import os
import re

from app import create_app, db
from models import Aplicacao, Produto
from validar_csv import validar_csv


def importar_pecas_de_csv(app, csv_path: str):
    """
    Importa produtos e aplicações de um arquivo CSV.
    Este script foi adaptado para ler o formato específico do arquivo 'export_pecas.csv',
    que possui uma coluna 'Aplicações' com múltiplos veículos separados por '|'.

    Ele adiciona novos produtos ou atualiza os existentes com base na coluna 'Código'.
    :param app: A instância da aplicação Flask.
    :param csv_path: O caminho para o arquivo CSV.
    """
    print(f"--- Iniciando importação do arquivo: {os.path.basename(csv_path)} ---")
    try:
        # 1. Validação prévia da estrutura do CSV
        if not validar_csv(csv_path):
            print("\nImportação cancelada devido a erros de validação no arquivo CSV.")
            return

        print(
            "\nValidação do CSV concluída. Iniciando a importação para o banco de dados..."
        )

        with app.app_context():
            # 2. Leitura do CSV
            try:
                # Tenta abrir com UTF-8, que é o ideal
                csvfile = open(
                    csv_path, "r", encoding="utf-8-sig", errors="strict", newline=""
                )
            except UnicodeDecodeError:
                # Se falhar, tenta com latin-1
                csvfile = open(
                    csv_path, "r", encoding="latin-1", errors="ignore", newline=""
                )
            with csvfile:
                reader = csv.DictReader(csvfile)
                rows = list(reader)
                if not rows:
                    print("Arquivo CSV está vazio. Nenhuma ação realizada.")
                    return

            total_linhas = len(rows)
            print(f"Encontradas {total_linhas} linhas de dados no CSV.")

            # 3. Cache de produtos existentes para otimização
            print("Mapeando produtos existentes no banco de dados...")
            codigos_csv = {
                row.get("codigo", "").strip().upper()
                for row in rows
                if row.get("codigo")
            }
            existing_products = {
                p.codigo: p
                for p in Produto.query.filter(Produto.codigo.in_(codigos_csv)).all()
            }

            print(
                f"Encontrados {len(existing_products)} produtos correspondentes no banco."
            )

            linhas_ignoradas = 0
            codigos_duplicados_csv = set()
            codigos_processados = set()

            produtos_adicionados = 0
            produtos_atualizados = 0

            # 4. Processamento: para cada linha, cria/atualiza Produto e suas Aplicacoes imediatamente
            print("Processando e salvando produtos um-a-um (modo seguro)...")

            for i, row in enumerate(rows):
                print(f"Processando [{i+1}/{total_linhas}]: ", end="")

                codigo = (row.get("codigo") or "").strip().upper()
                if not codigo:
                    print("Ignorado (código vazio).")
                    linhas_ignoradas += 1
                    continue

                if codigo in codigos_processados:
                    print(f"Ignorado (código '{codigo}' duplicado no CSV).")
                    codigos_duplicados_csv.add(codigo)
                    linhas_ignoradas += 1
                    continue
                codigos_processados.add(codigo)

                nome = (row.get("nome") or "").strip().upper()
                grupo = (row.get("grupo") or "").strip().upper()
                fornecedor = (row.get("fornecedor") or "").strip().upper()
                conversoes = (row.get("conversoes") or "").strip().upper()
                medidas = (row.get("medidas") or "").strip().upper()
                observacoes = (row.get("observacoes") or "").strip().upper()

                produto = existing_products.get(codigo)
                if produto:
                    # Atualiza campos
                    produto.nome = nome or produto.nome
                    produto.grupo = grupo or produto.grupo
                    produto.fornecedor = fornecedor or produto.fornecedor
                    produto.conversoes = conversoes or produto.conversoes
                    produto.medidas = medidas or produto.medidas
                    produto.observacoes = observacoes or produto.observacoes
                    produtos_atualizados += 1
                    print(f"Produto '{codigo}' atualizado.")
                else:
                    produto = Produto(
                        codigo=codigo,
                        nome=nome,
                        grupo=grupo,
                        fornecedor=fornecedor,
                        conversoes=conversoes,
                        medidas=medidas,
                        observacoes=observacoes,
                    )
                    db.session.add(produto)
                    # Força flush para obter id do produto antes de inserir aplicações
                    db.session.flush()
                    existing_products[codigo] = produto
                    produtos_adicionados += 1
                    print(f"Produto '{codigo}' criado.")

                # Processa aplicações: limpa as antigas e adiciona as novas
                # O CSV pode fornecer aplicações em duas formas:
                # - 'aplicacoes_json': uma string JSON com lista de objetos
                # - 'aplicacoes': uma string legível com itens separados por '|'.
                #   Ex: "FIORINO [1976/ 1989)  | 147 [1976/ 1989)"
                aplicacoes_data = []
                aplicacoes_json = row.get("aplicacoes_json")
                aplicacoes_text = row.get("aplicacoes")
                if aplicacoes_json:
                    try:
                        aplicacoes_data = json.loads(aplicacoes_json)
                    except (json.JSONDecodeError, TypeError):
                        aplicacoes_data = []
                elif aplicacoes_text:
                    # Parse textual field: separe por '|' e tente extrair montadora/veiculo/ano
                    # Usaremos heurísticas simples:
                    # - separa por '|'
                    # - tenta extrair ano entre '[' ']' ou '(' ')'
                    # - se houver coluna 'montadoras' no CSV, usaremos seu valor
                    #   como montadora para todas as aplicações da linha
                    parts = [p.strip() for p in aplicacoes_text.split("|") if p.strip()]
                    montadora_global = (
                        row.get("montadoras") or row.get("montadora") or ""
                    )
                    for part in parts:
                        veiculo = ""
                        ano = ""
                        motor = ""
                        conf_mtr = ""
                        # Extrai ano entre colchetes [] ou parênteses ()
                        m = re.search(r"\[(.*?)\]", part)
                        if not m:
                            m = re.search(r"\((.*?)\)", part)
                        if m:
                            ano = m.group(1).strip()
                            # remove a parte do ano do texto para deixar só o veículo + possivelmente motor
                            restante = re.sub(r"\[.*?\]|\(.*?\)", "", part).strip()
                        else:
                            restante = part

                        # Heurística para extrair motor/versão.
                        # Procura por tokens como: '1.0', '1.6', '16V', '8V', 'FLEX'
                        tokens = [t.strip() for t in restante.split() if t.strip()]
                        restante_tokens = []
                        for t in tokens:
                            # motor numérico tipo 1.0, 2.0
                            if re.match(r"^\d+\.\d+$", t):
                                motor = motor + (" " + t if motor else t)
                                continue
                            # v de válvulas, ex: 16V, 8V
                            if re.match(r"^\d+V$", t.upper()):
                                motor = motor + (" " + t if motor else t)
                                continue
                            # palavras comuns como FLEX, GAS, ALCOOL
                            if re.match(
                                r"^(FLEX|GAS|ALCOOL|DIESEL|MPI|FI|FI-E|INJETOR)$",
                                t.upper(),
                            ):
                                motor = motor + (" " + t if motor else t)
                                continue
                            # separe tokens que contenham hífen com números (ex: '1.6-16V')
                            if re.search(r"\d", t) and ("-" in t or "/" in t):
                                motor = motor + (" " + t if motor else t)
                                continue
                            restante_tokens.append(t)

                        # o que sobrou é tratado como veículo
                        veiculo = " ".join(restante_tokens).strip()

                        aplicacoes_data.append(
                            {
                                "veiculo": veiculo,
                                "ano": ano,
                                "motor": motor.strip(),
                                "conf_mtr": conf_mtr,
                                "montadora": montadora_global,
                            }
                        )

                if aplicacoes_data:
                    # Remove aplicações antigas do produto (se existirem)
                    db.session.query(Aplicacao).filter(
                        Aplicacao.produto_id == produto.id
                    ).delete(synchronize_session=False)
                    for app_data in aplicacoes_data:
                        campos_validos = {
                            k: str(v).strip().upper()
                            for k, v in app_data.items()
                            if k in ["veiculo", "ano", "motor", "conf_mtr", "montadora"]
                        }
                        if not campos_validos.get("veiculo"):
                            continue
                        nova_app = Aplicacao(produto_id=produto.id, **campos_validos)
                        db.session.add(nova_app)

                # Commit periódico para não acumular muitas operações em memória (ajustável)
                if (i + 1) % 200 == 0:
                    db.session.commit()

            # commit final
            db.session.commit()

            print("\n--- Importação Concluída com Sucesso! ---")
            print(f"Produtos novos adicionados: {produtos_adicionados}")
            print(f"Produtos existentes atualizados: {produtos_atualizados}")
            total_apps = (
                db.session.query(Aplicacao)
                .filter(
                    Aplicacao.produto_id.in_([p.id for p in existing_products.values()])
                )
                .count()
            )
            print(
                f"Aplicações atualmente no conjunto afetado: {total_apps}"
            )
            print(
                f"Linhas ignoradas (código vazio ou duplicado): {linhas_ignoradas}"
            )
            if codigos_duplicados_csv:
                print("  - Códigos duplicados no CSV: " + ", ".join(sorted(list(codigos_duplicados_csv))))

    except Exception as e:
        try:
            # Garante que a sessão seja revertida dentro do contexto da aplicação
            with app.app_context():
                db.session.rollback()
        except Exception:
            # Se não for possível abrir o context (caso raro), tenta rollback na sessão atual e segue
            try:
                db.session.rollback()
            except Exception:
                pass
        print(f"\n❌ ERRO FATAL durante a importação: {e}")
        print(
            "A transação foi revertida. Nenhuma alteração foi salva no banco de dados."
        )


if __name__ == "__main__":
    csv_filename = "export_pecas.csv"
    csv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), csv_filename)

    app = create_app()
    with app.app_context():
        importar_pecas_de_csv(app, csv_path)
