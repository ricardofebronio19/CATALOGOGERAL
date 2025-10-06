import csv
import os
from app import app, db, Produto, Aplicacao, inicializar_banco, _normalize_for_search


def importar_pecas():
    """
    Importa produtos e aplicações de um arquivo 'produto.csv' estruturado.
    O script usa o DictReader do módulo csv para ler os dados e popular o banco.
    Ele adiciona novos produtos ou atualiza os existentes com base na coluna 'CODIGO'.
    """
    csv_filename = 'produto.csv'
    CSV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), csv_filename)

    if not os.path.exists(CSV_PATH):
        print(f"Erro: Arquivo '{csv_filename}' não encontrado no diretório do script.")
        return

    with app.app_context():
        # Garante que as tabelas do banco de dados existam antes de importar
        print("Verificando e inicializando o banco de dados...")
        inicializar_banco()

        try:
            # Usar TextIOWrapper para ler o arquivo com a codificação correta (latin-1)
            # e detectar o dialeto (delimitador) automaticamente.
            with open(CSV_PATH, 'r', encoding='latin-1', errors='ignore', newline='') as csvfile:
                print(f"Iniciando importação de '{csv_filename}'...")
                
                # Detecta o delimitador (provavelmente ';')
                try:
                    dialect = csv.Sniffer().sniff(csvfile.read(2048))
                    csvfile.seek(0)
                except csv.Error:
                    print("Não foi possível detectar o delimitador. Usando ';' como padrão.")
                    csv.register_dialect('semicolon', delimiter=';')
                    dialect = 'semicolon'
                    csvfile.seek(0)

                reader = csv.DictReader(csvfile, dialect=dialect)

                # Normaliza os nomes das colunas para busca flexível
                reader.fieldnames = [_normalize_for_search(str(field)) for field in reader.fieldnames]

                produtos_adicionados = 0
                produtos_atualizados = 0

                for i, row in enumerate(reader, 1):
                    codigo = (row.get('codigo') or '').strip().upper()
                    if not codigo:
                        print(f"AVISO: Linha {i} ignorada por não ter um código.")
                        continue

                    produto = Produto.query.filter_by(codigo=codigo).first()

                    if not produto:
                        produto = Produto(codigo=codigo)
                        db.session.add(produto)
                        produtos_adicionados += 1
                    else:
                        produtos_atualizados += 1

                    # Atualiza os dados do produto
                    produto.nome = (row.get('nome') or '').strip().upper()
                    produto.fornecedor = (row.get('fabricante') or '').strip().upper()
                    produto.medidas = (row.get('medidas') or '').strip()
                    
                    # Limpa aplicações antigas para evitar duplicatas na atualização
                    produto.aplicacoes.clear()

                    # Adiciona a nova aplicação
                    nova_aplicacao = Aplicacao(
                        montadora=(row.get('monatadora') or '').strip().upper(),
                        veiculo=(row.get('veiculo') or '').strip().upper(),
                        motor=(row.get('observacao') or '').strip().upper(), # Usando 'OBSERVAÇÃO' como 'motor'
                        ano=(row.get('ano') or '').strip()
                    )
                    produto.aplicacoes.append(nova_aplicacao)

                db.session.commit()

                print("\nImportação concluída!")
                print(f"Produtos novos adicionados: {produtos_adicionados}")
                print(f"Produtos existentes atualizados: {produtos_atualizados}")

        except Exception as e:
            db.session.rollback()
            print(f"Ocorreu um erro durante a importação: {e}")
            return

if __name__ == '__main__':
    importar_pecas()
