import os
import shutil
from datetime import datetime
from urllib.parse import urlparse

import requests
from werkzeug.utils import secure_filename

from app import db
from models import ImagemProduto, Produto

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}


def download_image_from_url(
    url: str, upload_folder: str, product_code: str = None
) -> str | None:
    """
    Baixa uma imagem de uma URL, a salva na pasta de uploads com um nome seguro
    e retorna o nome do arquivo salvo.

    :param url: A URL da imagem a ser baixada.
    :param upload_folder: O caminho para a pasta onde a imagem será salva.
    :param product_code: O código do produto, usado para nomear o arquivo (opcional).
    :return: O nome do arquivo salvo ou None em caso de falha.
    """
    if not url or not url.startswith(("http://", "https://")):
        return None

    try:
        response = requests.get(
            url, stream=True, timeout=10, headers={"User-Agent": "Mozilla/5.0"}
        )
        response.raise_for_status()

        # Tenta obter a extensão do arquivo a partir da URL
        path = urlparse(url).path
        ext = os.path.splitext(path)[1].lower().strip(".")
        
        # Se não conseguir da URL, tenta do filename na URL
        if ext not in ALLOWED_EXTENSIONS:
            original_filename = url.split("/")[-1].split("?")[0]
            _, ext_from_name = os.path.splitext(original_filename)
            ext = ext_from_name.lower().strip(".")
            
        # Se ainda não conseguir, usa o Content-Type
        if ext not in ALLOWED_EXTENSIONS:
            content_type = response.headers.get("content-type", "").split("/")
            if content_type[0] == "image" and len(content_type) > 1:
                ext = content_type[1]
                if ext == "jpeg":
                    ext = "jpg"
            else:
                ext = "jpg"  # Fallback padrão
                
        # Garante que a extensão é válida
        if ext not in ALLOWED_EXTENSIONS:
            return None

        base_name = product_code if product_code else "img"
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
        filename = secure_filename(f"{base_name}_{timestamp}.{ext}")
        filepath = os.path.join(upload_folder, filename)

        with open(filepath, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        return filename
    except requests.exceptions.RequestException as e:
        print(f"Erro ao baixar a imagem da URL {url}: {e}")
        return None
    except Exception as e:
        print(f"Erro inesperado ao processar a imagem da URL {url}: {e}")
        return None


def vincular_imagens_por_codigo(app):
    """
    Varre a pasta de uploads e vincula as imagens aos produtos correspondentes.
    O vínculo é feito se o nome do arquivo de imagem (sem a extensão) for igual
    ao código de um produto existente no banco de dados.

    :param app: A instância da aplicação Flask.
    """
    from app import UPLOAD_FOLDER

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
        produtos_map = {p.codigo: p for p in Produto.query.all()}
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

            # Tentativa de extrair o código do produto de nomes gerados pelo app
            # (ex: CODIGO_20231010120000000000.jpg). Se houver um underscore seguido de timestamp,
            # pegamos a parte antes do primeiro underscore.
            codigo_base = codigo_produto.split("_")[0]
            produto = produtos_map.get(codigo_base)

            if not produto:
                print("Ignorado (produto não encontrado).")
                produtos_nao_encontrados += 1
                codigos_nao_encontrados.add(codigo_base)
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
        print(f"Produtos não encontrados (códigos sem correspondência): {produtos_nao_encontrados}")
        
        if codigos_nao_encontrados:
            sample = ", ".join(sorted(list(codigos_nao_encontrados))[:10])
            more = "..." if len(codigos_nao_encontrados) > 10 else ""
            print(f"  - Códigos não encontrados: {sample}{more}")

        return imagens_vinculadas
