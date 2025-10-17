import os
import requests
from datetime import datetime
from werkzeug.utils import secure_filename
from urllib.parse import urlparse

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def download_image_from_url(url: str, upload_folder: str, product_code: str) -> str | None:
    """
    Baixa uma imagem de uma URL, a salva na pasta de uploads com um nome seguro
    e retorna o nome do arquivo salvo.

    :param url: A URL da imagem a ser baixada.
    :param upload_folder: O caminho para a pasta onde a imagem será salva.
    :param product_code: O código do produto, usado para nomear o arquivo.
    :return: O nome do arquivo salvo ou None em caso de falha.
    """
    if not url:
        return None

    try:
        response = requests.get(url, stream=True, timeout=10)
        response.raise_for_status()

        # Tenta obter a extensão do arquivo a partir da URL
        path = urlparse(url).path
        ext = os.path.splitext(path)[1].lower().strip('.')
        if ext not in ALLOWED_EXTENSIONS:
            # Se a URL não tiver uma extensão válida, tenta usar o 'Content-Type'
            content_type = response.headers.get('content-type', '').split('/')
            if content_type[0] == 'image' and content_type[1] in ALLOWED_EXTENSIONS:
                ext = content_type[1]
            else:
                return None # Extensão não permitida ou não encontrada

        timestamp = datetime.now().strftime('%Y%m%d%H%M%S%f')
        filename = secure_filename(f"{product_code}_{timestamp}.{ext}")
        filepath = os.path.join(upload_folder, filename)
        
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        return filename
    except requests.exceptions.RequestException as e:
        print(f"Erro ao baixar a imagem da URL {url}: {e}")
        return None
    except Exception as e:
        print(f"Erro inesperado ao processar a imagem da URL {url}: {e}")
        return None