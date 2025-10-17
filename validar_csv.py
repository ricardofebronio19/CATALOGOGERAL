import csv
import os

def validar_csv(filepath_entrada: str):
    """
    Valida a estrutura de um arquivo CSV antes da importação.

    Verifica:
    1. Se o arquivo existe.
    2. Se a codificação é compatível (lê como utf-8-sig).
    3. Se o cabeçalho tem o número e os nomes de colunas esperados.
    4. Se cada linha tem o mesmo número de colunas que o cabeçalho.
    5. Se colunas obrigatórias (como 'Código') não estão vazias.
    """
    print(f"--- Iniciando validação e correção do arquivo: {os.path.basename(filepath_entrada)} ---")

    # 1. Validação de Existência do Arquivo
    if not os.path.exists(filepath_entrada):
        print(f"❌ ERRO: Arquivo não encontrado em '{filepath_entrada}'")
        return False

    print("✅ Arquivo encontrado.")

    # Colunas obrigatórias esperadas no cabeçalho
    # Aceitamos tanto 'aplicacoes_json' (formato JSON) quanto 'aplicacoes' (texto legível separado por '|')
    colunas_obrigatorias = {'codigo', 'nome'}
    errors = []

    try:
        try:
            # Tenta abrir com UTF-8, que é o ideal
            csvfile = open(filepath_entrada, 'r', encoding='utf-8-sig', errors='strict', newline='')
        except UnicodeDecodeError:
            # Se falhar, tenta com latin-1, comum em arquivos gerados no Windows/Excel
            print("⚠️  Aviso: O arquivo não está em UTF-8. Tentando abrir como latin-1.")
            csvfile = open(filepath_entrada, 'r', encoding='latin-1', errors='ignore', newline='')

        with csvfile:
            print("✅ Arquivo aberto com sucesso (codificação compatível).")

            # Usamos DictReader para validar pelo nome da coluna, não pela posição
            reader = csv.DictReader(csvfile)

            # 2. Validação do Cabeçalho
            header = reader.fieldnames
            if not header:
                print("❌ ERRO: O arquivo CSV está vazio ou não tem cabeçalho.")
                return False

            colunas_faltando = colunas_obrigatorias - set(header)
            if colunas_faltando:
                errors.append(f"Linha 1 (Cabeçalho): Colunas obrigatórias não encontradas: {', '.join(sorted(list(colunas_faltando)))}")

            if not errors: # Só continua se o cabeçalho for válido
                print("✅ Cabeçalho validado com sucesso.")

                # 3. Validação das Linhas de Dados
                for i, row in enumerate(reader, 2): # Começa da linha 2 do arquivo
                    # Ignora linhas completamente vazias
                    if not any(row.values()):
                        continue

                    # Verifica se o código está preenchido
                    codigo = row.get('codigo', '').strip()
                    if not codigo:
                        errors.append(f"Linha {i}: A coluna 'codigo' está vazia.")

                    # Verifica se o nome está preenchido
                    nome = row.get('nome', '').strip()
                    if not nome:
                        errors.append(f"Linha {i}: A coluna 'nome' está vazia para o código '{codigo}'.")

    except Exception as e:
        print(f"❌ ERRO FATAL: Não foi possível processar o arquivo. Erro: {e}")
        return False

    # 4. Relatório Final
    print("\n--- Relatório da Validação ---")
    if not errors:
        print("🎉 SUCESSO: Nenhuma inconsistência encontrada. O arquivo parece estar pronto para importação.")
        return True
    else:
        print(f"❌ ERRO: Foram encontrados {len(errors)} problemas no arquivo.")
        # Mostra os primeiros 20 erros para não poluir o console
        for error_msg in errors[:20]:
            print(f"  - {error_msg}")
        if len(errors) > 20:
            print(f"  ... e mais {len(errors) - 20} outros erros.")
        print("\nPor favor, corrija os problemas listados acima no arquivo CSV e tente novamente.")
        return False