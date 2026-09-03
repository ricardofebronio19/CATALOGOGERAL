import mimetypes
import os
import re
from datetime import datetime
from urllib.parse import urlparse

import requests
from werkzeug.utils import secure_filename

from core_utils import allowed_file


def _extension_from_content_type(ct: str | None) -> str | None:
    if not ct:
        return None
    ext = mimetypes.guess_extension(ct.split(";")[0].strip())
    if ext:
        return ext.lstrip(".")
    # Fallback common mappings
    if ct.startswith("image/jpeg"):
        return "jpg"
    if ct.startswith("image/png"):
        return "png"
    if ct.startswith("image/gif"):
        return "gif"
    if ct.startswith("image/webp"):
        return "webp"
    return None


def download_image_from_url(url: str, dest_dir: str, product_code: str | None = None, timeout: int = 10) -> str | None:
    """Baixa uma imagem de `url` para `dest_dir` retornando o nome do arquivo salvo.

    Retorna `None` em caso de falha ou se a extensão não for permitida.
    """
    try:
        resp = requests.get(url, stream=True, timeout=timeout)
        if resp.status_code != 200:
            return None

        # Tenta inferir a extensão a partir da URL primeiro, depois do content-type
        ext = _extension_from_url(url) or _extension_from_content_type(resp.headers.get("content-type"))
        if not ext:
            return None

        # Normaliza extensão
        ext = ext.lower().lstrip(".")

        # Verifica se é permitido
        if not allowed_file(f"dummy.{ext}"):
            return None

        timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
        base = product_code or "img"
        filename = secure_filename(f"{base}_{timestamp}.{ext}")

        os.makedirs(dest_dir, exist_ok=True)
        dest_path = os.path.join(dest_dir, filename)

        with open(dest_path, "wb") as fh:
            for chunk in resp.iter_content(chunk_size=8192):
                if chunk:
                    fh.write(chunk)

        return filename
    except Exception:
        return None


def vincular_imagens_por_codigo(app) -> int:
    """Varre a pasta de uploads e associa imagens aos produtos pelo código no nome do arquivo.

    A função é resiliente a cenários sem uploads, sem app configurada ou sem banco
    inicializado, retornando 0 nesses casos.
    """
    if app is None:
        return 0

    upload_folder = app.config.get("UPLOAD_FOLDER")
    if not upload_folder or not os.path.isdir(upload_folder):
        return 0

    try:
        from app import db
        from models import ImagemProduto, Produto
    except Exception:
        return 0

    linked_count = 0

    with app.app_context():
        for filename in sorted(os.listdir(upload_folder)):
            if not filename or filename.startswith("."):
                continue

            stem = os.path.splitext(filename)[0]
            if not stem:
                continue

            if not allowed_file(filename):
                continue

            code_candidate = None
            for token in re.split(r"[_\-. ]+", stem):
                normalized_token = re.sub(r"[^A-Za-z0-9]", "", token)
                if not normalized_token:
                    continue
                lowered = normalized_token.lower()
                if lowered in {"img", "image", "foto", "photo", "imagem"}:
                    continue
                if re.search(r"[A-Za-z]", normalized_token) and re.search(r"\d", normalized_token):
                    code_candidate = normalized_token
                    break
                if len(normalized_token) >= 3 and re.search(r"[A-Za-z]", normalized_token):
                    code_candidate = normalized_token
                    break

            if not code_candidate:
                continue

            produto = Produto.query.filter(
                db.or_(
                    Produto.codigo.ilike(code_candidate),
                    Produto.codigo.ilike(f"%{code_candidate}%"),
                    Produto.codigo.ilike(f"%{code_candidate.replace('-', '')}%"),
                )
            ).first()

            if produto is None:
                continue

            existing = ImagemProduto.query.filter_by(produto_id=produto.id, filename=filename).first()
            if existing is not None:
                continue

            db.session.add(
                ImagemProduto(produto_id=produto.id, filename=filename, ordem=0)
            )
            linked_count += 1

        if linked_count:
            db.session.commit()

    return linked_count
