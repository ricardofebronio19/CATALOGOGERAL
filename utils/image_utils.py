import os
import shutil
from datetime import datetime

import requests
from werkzeug.utils import secure_filename

from app import db
from models import ImagemProduto, Produto


def download_image_from_url(
    url: str, upload_folder: str, product_code: str = None
) -> str | None:
    """Baixa uma imagem de uma URL e a salva na pasta de uploads."""
    if not url or not url.startswith(("http://", "https://")):
        return None
    try:
        response = requests.get(
            url, stream=True, timeout=10, headers={"User-Agent": "Mozilla/5.0"}
        )
        response.raise_for_status()

        original_filename = url.split("/")[-1].split("?")[0]
        _, ext = os.path.splitext(original_filename)
        if ext.lower() not in [".jpg", ".jpeg", ".png", ".gif", ".webp"]:
            content_type = response.headers.get("content-type")
            ext = (
                "." + content_type.split("/")[1]
                if content_type and "image" in content_type
                else ".jpg"
            )

        base_name = product_code if product_code else "img"
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
        filename = secure_filename(f"{base_name}_{timestamp}{ext}")

        filepath = os.path.join(upload_folder, filename)
        with open(filepath, "wb") as f:
            shutil.copyfileobj(response.raw, f)
        return filename
    except requests.exceptions.RequestException as e:
        print(f"Erro ao baixar a imagem da URL {url}: {e}")
        return None


def vincular_imagens_por_codigo(app):
    """Varre a pasta de uploads e vincula imagens aos produtos por código."""
    from ..app import ALLOWED_EXTENSIONS, UPLOAD_FOLDER

    print("Iniciando o processo de vinculação de imagens...")

    with app.app_context():
        produtos_map = {p.codigo: p for p in Produto.query.all()}
        imagens_existentes = {img.filename for img in ImagemProduto.query.all()}

        vinculadas = 0
        for filename in os.listdir(UPLOAD_FOLDER):
            codigo_produto, ext = os.path.splitext(filename)
            if ext.lower().strip(".") not in ALLOWED_EXTENSIONS:
                continue

            # Tentativa de extrair o código do produto de nomes gerados pelo app
            # (ex: CODIGO_20231010120000000000.jpg). Se houver um underscore seguido de timestamp,
            # pegamos a parte antes do primeiro underscore.
            codigo_base = codigo_produto.split("_")[0]
            produto = produtos_map.get(codigo_base)
            if produto and filename not in imagens_existentes:
                nova_imagem = ImagemProduto(produto_id=produto.id, filename=filename)
                db.session.add(nova_imagem)
                vinculadas += 1

        db.session.commit()
        print(f"Processo concluído. {vinculadas} novas imagens foram vinculadas.")
