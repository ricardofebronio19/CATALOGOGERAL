import mimetypes
import os
from datetime import datetime
from urllib.parse import urlparse

import requests
from werkzeug.utils import secure_filename

from core_utils import allowed_file


def _extension_from_url(url: str) -> str | None:
    try:
        path = urlparse(url).path
        _, ext = os.path.splitext(path)
        if ext:
            return ext.lstrip(".")
    except Exception:
        return None
    return None


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
