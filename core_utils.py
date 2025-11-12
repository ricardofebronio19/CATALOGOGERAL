import time
import unicodedata
from threading import Lock

from sqlalchemy import func

# Importações relativas para evitar dependência circular
from app import db
from models import Aplicacao, Produto

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}


def _normalize_for_search(text: str) -> str:
    """Remove acentos, pontuações comuns e converte para minúsculas para busca."""
    if not text:
        return ""
    nfkd_form = unicodedata.normalize("NFD", text.lower())
    text = "".join([c for c in nfkd_form if not unicodedata.combining(c)])
    return text.replace(".", "").replace("-", "").replace(",", "").replace(" ", "")


def _apply_db_normalization(column):
    """Aplica funções SQL para normalizar uma coluna para busca (case, acentos, pontuação)."""
    normalized_column = func.lower(column)
    # Mapa ampliado de caracteres acentuados para suportar vários idiomas
    accent_map = {
        # a
        "á": "a",
        "à": "a",
        "â": "a",
        "ã": "a",
        "ä": "a",
        "å": "a",
        "æ": "ae",
        # c
        "ç": "c",
        # e
        "é": "e",
        "è": "e",
        "ê": "e",
        "ë": "e",
        # i
        "í": "i",
        "ì": "i",
        "î": "i",
        "ï": "i",
        # o
        "ó": "o",
        "ò": "o",
        "ô": "o",
        "õ": "o",
        "ö": "o",
        "ø": "o",
        "œ": "oe",
        # u
        "ú": "u",
        "ù": "u",
        "û": "u",
        "ü": "u",
        # n
        "ñ": "n",
        # y
        "ý": "y",
        "ÿ": "y",
    }
    for accented, unaccented in accent_map.items():
        normalized_column = func.replace(normalized_column, accented, unaccented)
    return func.replace(
        func.replace(
            func.replace(func.replace(normalized_column, ".", ""), "-", ""), ",", ""
        ),
        " ",
        "",
    )


def _build_search_query(
    termo, codigo_produto, montadora, aplicacao_termo, grupo, medidas
):
    """Constrói a query de busca de produtos com base nos filtros fornecidos."""
    query = Produto.query

    if termo:
        query = query.join(
            Aplicacao, Produto.id == Aplicacao.produto_id, isouter=True
        ).distinct()
        for palavra in termo.strip().split():
            # Usa busca simples com ilike para evitar SQL muito complexo
            query = query.filter(
                db.or_(
                    Produto.nome.ilike(f"%{palavra}%"),
                    Produto.codigo.ilike(f"%{palavra}%"),
                    Produto.fornecedor.ilike(f"%{palavra}%"),
                    Aplicacao.veiculo.ilike(f"%{palavra}%"),
                    Aplicacao.motor.ilike(f"%{palavra}%"),
                    Produto.conversoes.ilike(f"%{palavra}%"),
                )
            )

    if codigo_produto:
        query = query.filter(Produto.codigo.ilike(f"%{codigo_produto}%"))

    if grupo:
        query = query.filter(Produto.grupo.ilike(f"%{grupo}%"))

    if medidas:
        query = query.filter(Produto.medidas.ilike(f"%{medidas}%"))

    needs_join = not termo and (montadora or aplicacao_termo)
    if needs_join:
        query = query.join(Aplicacao, Produto.id == Aplicacao.produto_id)

    if montadora:
        # Se o usuário passou também uma aplicação (veículo), preferimos
        # filtrar por aplicação no SQL e aplicar a filtragem por montadora no
        # nível da aplicação (Python). Isso contorna limitações de LIKE/NOCASE
        # do SQLite com caracteres Unicode/diacríticos.
        if aplicacao_termo:
            # Não aplicar filtro de montadora no SQL, deixamos para o
            # pós-processamento em `routes.buscar` onde faremos uma
            # comparação normalizada (sem acentos).
            pass
        else:
            # A busca com `ilike` é geralmente suficiente para a maioria dos casos
            # e funciona bem com a normalização de caracteres do SQLite.
            query = query.filter(Aplicacao.montadora.ilike(f"%{montadora}%"))

    if aplicacao_termo:
        aplicacao_like = f"%{aplicacao_termo}%"
        query = query.filter(
            db.or_(
                Aplicacao.veiculo.ilike(aplicacao_like),
                Aplicacao.motor.ilike(aplicacao_like),
            )
        )

    return query


def _atualizar_similares_simetricamente(produto_principal, novos_similares):
    """Atualiza a relação de similares de forma simétrica."""
    similares_antigos = set(produto_principal.similares)
    novos_similares_set = set(novos_similares)

    produto_principal.similares = novos_similares

    for similar_removido in similares_antigos - novos_similares_set:
        if produto_principal in similar_removido.similares:
            similar_removido.similares.remove(produto_principal)

    for novo_similar in novos_similares:
        if produto_principal not in novo_similar.similares:
            novo_similar.similares.append(produto_principal)


# --- Cache para Datalists ---
_datalist_cache = {}
_cache_lock = Lock()
CACHE_TIMEOUT_SECONDS = 300  # 5 minutos


def _get_form_datalists(app_context=None):
    """
    Busca dados para preencher os datalists nos formulários de produto.
    Utiliza um cache em memória para evitar consultas repetitivas ao banco de dados,
    melhorando significativamente o tempo de carregamento dos formulários.
    Opcionalmente, aceita um contexto de aplicação para ser usado fora de uma requisição Flask.
    """
    global _datalist_cache
    now = time.time()

    def query_data():
        """Função interna para executar as queries ao banco de dados."""
        from app import MONTADORAS_PREDEFINIDAS

        grupos_db = (
            db.session.query(Produto.grupo)
            .distinct()
            .filter(Produto.grupo.isnot(None), Produto.grupo != "")
            .order_by(Produto.grupo)
            .all()
        )
        lista_grupos = sorted([g[0] for g in grupos_db])

        fornecedores_db = (
            db.session.query(Produto.fornecedor)
            .distinct()
            .filter(Produto.fornecedor.isnot(None), Produto.fornecedor != "")
            .order_by(Produto.fornecedor)
            .all()
        )
        lista_fornecedores = sorted([f[0] for f in fornecedores_db])

        montadoras_db = (
            db.session.query(Aplicacao.montadora)
            .distinct()
            .filter(Aplicacao.montadora.isnot(None), Aplicacao.montadora != "")
            .all()
        )
        lista_montadoras_db = [m[0] for m in montadoras_db]
        lista_montadoras_completa = sorted(
            list(set(lista_montadoras_db + MONTADORAS_PREDEFINIDAS))
        )
        return {
            "grupos": lista_grupos,
            "fornecedores": lista_fornecedores,
            "montadoras": lista_montadoras_completa,
        }

    with _cache_lock:
        # Verifica se o cache existe e não expirou
        if (
            _datalist_cache
            and (now - _datalist_cache.get("timestamp", 0)) < CACHE_TIMEOUT_SECONDS
        ):
            return _datalist_cache["data"]

        # Armazena os novos dados e o timestamp no cache
        _datalist_cache = {"timestamp": now, "data": query_data()}
        return _datalist_cache["data"]


def _parse_year_range(year_str: str | None) -> tuple[int, int]:
    """Converte uma string de ano (ex: "2010", "2010/2015", "2018/...") em uma tupla."""
    if not year_str or not year_str.strip():
        return -1, -1
    year_str = year_str.strip()
    try:
        if year_str.endswith("/...") or year_str.endswith("/"):
            return int(year_str.split("/")[0]), 9999
        if year_str.startswith(".../") or year_str.startswith("/"):
            return 0, int(year_str.split("/")[1])
        if "/" in year_str:
            parts = year_str.split("/")
            return min(int(parts[0]), int(parts[1])), max(int(parts[0]), int(parts[1]))
        return int(year_str), int(year_str)
    except (ValueError, IndexError):
        return -1, -1


def _ranges_overlap(range1: tuple[int, int], range2: tuple[int, int]) -> bool:
    """Verifica se dois intervalos de anos se sobrepõem."""
    return range1[0] <= range2[1] and range2[0] <= range1[1]


def allowed_file(filename):
    """Função para verificar se a extensão do arquivo é permitida."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
