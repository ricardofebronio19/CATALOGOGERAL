import csv
import os
import re


def limpar_valor(valor: str) -> str:
    """
    Remove aspas extras, espaços em excesso e caracteres problemáticos.
    Ex: '""FIAT""' -> 'FIAT'
    """
    # Remove aspas do início e do fim e espaços em branco
    valor = valor.strip().strip('"')
    # Remove aspas duplas que podem ter ficado no meio
    valor = valor.replace('""', '"')
    return valor.strip()


def extrair_ano(texto_aplicacao: str) -> tuple[str, str]:
    """
    Encontra um padrão de ano como [1983/ 1989) e o formata para 1983/1989.
    Retorna o texto da aplicação sem o ano e o ano formatado.
    """
    match = re.search(r"\[(.*?)\]", texto_aplicacao)
    if match:
        # Pega o conteúdo de dentro dos colchetes
        ano_bruto = match.group(1)
        # Remove o padrão de ano da string original
        texto_limpo = texto_aplicacao.replace(match.group(0), "").strip()

        # Formata a string de ano: '1983/ 1989)' -> '1983/1989'
        ano_formatado = ano_bruto.replace(")", "").replace(" ", "").strip()
        return texto_limpo, ano_formatado

    return texto_aplicacao.strip(), ""


def organizar_csv(arquivo_entrada: str, arquivo_saida: str):
    """
    Lê um arquivo CSV com formatação complexa, limpa os dados e
    gera um novo arquivo CSV pronto para importação.
    """
    print(f"--- Iniciando a organização do arquivo: {arquivo_entrada} ---")

    if not os.path.exists(arquivo_entrada):
        print(f"❌ ERRO: Arquivo de entrada '{arquivo_entrada}' não encontrado.")
        return

    linhas_processadas = 0
    linhas_gravadas = 0

    # Regex para separar os campos, considerando que eles podem estar entre aspas duplas ("")
    # e são separados por vírgulas.
    # Captura o conteúdo dentro das aspas ou o conteúdo até a próxima vírgula.
    csv_pattern = re.compile(r'""([^"]*)""|([^,]+)')

    try:
        with open(
            arquivo_entrada, "r", encoding="latin-1", errors="ignore"
        ) as f_entrada, open(
            arquivo_saida, "w", encoding="utf-8", newline=""
        ) as f_saida:

            # Define o cabeçalho do novo arquivo de saída
            cabecalho_saida = [
                "codigo",
                "nome",
                "fornecedor",
                "grupo",
                "aplicacoes_completas",
            ]
            writer = csv.writer(f_saida)
            writer.writerow(cabecalho_saida)

            # Pula o cabeçalho do arquivo de entrada
            next(f_entrada, None)

            for i, linha_bruta in enumerate(f_entrada, 2):
                # Remove aspas do início/fim da linha e espaços em branco
                linha_limpa = linha_bruta.strip().strip('"')
                if not linha_limpa:
                    continue

                # Usa a regex para extrair os campos da linha
                linha = [
                    (m.group(1) or m.group(2) or "")
                    for m in csv_pattern.finditer(linha_limpa)
                ]

                linhas_processadas += 1
                if len(linha) < 6:
                    print(f"⚠️  Aviso: Linha {i} ignorada por ter menos de 6 colunas.")
                    continue

                # Extrai e limpa os valores de cada coluna
                codigo = limpar_valor(linha[0])
                nome = limpar_valor(linha[1])
                fornecedor = limpar_valor(linha[2])
                montadora_geral = limpar_valor(linha[3])
                grupo = limpar_valor(linha[4])
                aplicacoes_brutas = limpar_valor(linha[5])

                if not codigo:
                    print(f"⚠️  Aviso: Linha {i} ignorada por não ter código.")
                    continue

                # Monta a string de 'aplicacoes_completas'
                aplicacoes_finais = []
                for app_str in aplicacoes_brutas.split("|"):
                    app_str = app_str.strip()
                    if not app_str or app_str == "/":
                        continue

                    veiculo, ano = extrair_ano(app_str)

                    # Constrói a aplicação final no formato "MONTADORA-VEICULO ANO"
                    montadora = (
                        montadora_geral if montadora_geral else "FIAT"
                    )  # Padrão para FIAT se vazio

                    aplicacao_final = f"{montadora}-{veiculo} {ano}".strip()
                    aplicacoes_finais.append(aplicacao_final)

                # Junta todas as aplicações com '|'
                texto_aplicacoes_completas = " | ".join(aplicacoes_finais)

                # Escreve a linha limpa no novo arquivo
                writer.writerow(
                    [codigo, nome, fornecedor, grupo, texto_aplicacoes_completas]
                )
                linhas_gravadas += 1

        print("\n--- ✅ Processo Concluído ---")
        print(f"Total de linhas lidas: {linhas_processadas}")
        print(f"Total de produtos gravados: {linhas_gravadas}")
        print(
            f"Arquivo '{arquivo_saida}' foi gerado com sucesso e está pronto para importação!"
        )

    except Exception as e:
        print(f"❌ ERRO FATAL durante o processamento: {e}")


if __name__ == "__main__":
    organizar_csv("export_pecas.csv", "pecas_para_importar.csv")
