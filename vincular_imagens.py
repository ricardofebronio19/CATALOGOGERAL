import os

from app import ALLOWED_EXTENSIONS, UPLOAD_FOLDER, create_app, db
from models import ImagemProduto, Produto


def vincular_imagens_por_codigo(app):
    """
    Varre a pasta de uploads e vincula as imagens aos produtos correspondentes.
    O vínculo é feito se o nome do arquivo de imagem (sem a extensão) for igual
    ao código de um produto existente no banco de dados.

    :param app: A instância da aplicação Flask.
    """
    print("Iniciando o processo de vinculação de imagens...")

    if not os.path.isdir(UPLOAD_FOLDER):
        print(f"ERRO: A pasta de uploads não foi encontrada em '{UPLOAD_FOLDER}'.")
        return

    with app.app_context():
        imagens_vinculadas = 0
        produtos_nao_encontrados = 0
        imagens_ja_existentes = 0
        arquivos_ignorados = 0
        codigos_nao_encontrados = set()

        # Otimização: Carrega todos os produtos e seus vínculos de imagem existentes em memória
        print("Carregando produtos e imagens existentes do banco de dados...")
        # Carrega todos os produtos em um dicionário para acesso rápido
        produtos_map = {p.codigo: p for p in Produto.query.all()}
        # Carrega todos os nomes de arquivos de imagem existentes em um conjunto para verificação rápida
        imagens_existentes = {img.filename for img in ImagemProduto.query.all()}
        print("Carregamento concluído.")

        # Lista todos os arquivos na pasta de uploads
        nomes_arquivos = os.listdir(UPLOAD_FOLDER)
        total_arquivos = len(nomes_arquivos)
        print(f"Encontrados {total_arquivos} arquivos na pasta de uploads.")

        for i, filename in enumerate(nomes_arquivos):
            # Extrai o nome do arquivo e a extensão
            codigo_produto, ext = os.path.splitext(filename)
            ext = ext.lower().strip(".")

            # Imprime o progresso
            print(f"Processando [{i+1}/{total_arquivos}]: {filename} ... ", end="")

            # Verifica se é uma extensão de imagem permitida
            if ext not in ALLOWED_EXTENSIONS:
                print("Ignorado (não é uma imagem).")
                arquivos_ignorados += 1
                continue

            # Busca o produto pelo código (nome do arquivo)
            produto = produtos_map.get(codigo_produto)

            if not produto:
                print("Ignorado (produto não encontrado).")
                produtos_nao_encontrados += 1
                codigos_nao_encontrados.add(codigo_produto)
                continue

            # Verifica se a imagem já está vinculada (em qualquer produto)
            if filename in imagens_existentes:
                print("Ignorado (já vinculado).")
                imagens_ja_existentes += 1
                continue

            # Cria o novo vínculo
            nova_imagem = ImagemProduto(produto_id=produto.id, filename=filename)
            db.session.add(nova_imagem)
            imagens_vinculadas += 1
            print("Vinculado com sucesso!")

            # Commit periódico a cada 500 novas imagens para liberar memória da sessão
            if imagens_vinculadas % 500 == 0:
                db.session.commit()

        # Faz o commit de todas as novas vinculações no banco de dados
        db.session.commit()

        print("\n--- Processo Concluído ---")
        print(f"Imagens vinculadas com sucesso: {imagens_vinculadas}")
        print(f"Imagens que já estavam vinculadas: {imagens_ja_existentes}")
        print(f"Arquivos ignorados (extensão inválida): {arquivos_ignorados}")
        print(
            "Produtos não encontrados (códigos sem correspondência): "
            + str(produtos_nao_encontrados)
        )
        if codigos_nao_encontrados:
            sample = ", ".join(sorted(list(codigos_nao_encontrados))[:10])
            more = "..." if len(codigos_nao_encontrados) > 10 else ""
            print(f"  - Códigos não encontrados: {sample}{more}")


if __name__ == "__main__":
    app = create_app()
    # Este script agora deve ser executado através do comando 'link-images' em run.py
    print("Este script foi movido para um comando CLI.")
    print("Use: python run.py link-images")
