import os
import re
import shutil
import unicodedata
from datetime import datetime
import requests
from sqlalchemy import func
from werkzeug.utils import secure_filename

from app import db, Produto, Aplicacao, MONTADORAS_PREDEFINIDAS

def _normalize_for_search(text: str) -> str:
    """Remove acentos, pontuações comuns e converte para minúsculas para busca."""
    if not text:
        return ""
    nfkd_form = unicodedata.normalize('NFD', text.lower())
    text = "".join([c for c in nfkd_form if not unicodedata.combining(c)])
    return text.replace('.', '').replace('-', '').replace(',', '').replace(' ', '')

def _apply_db_normalization(column):
    """Aplica funções SQL para normalizar uma coluna para busca (case, acentos, pontuação)."""
    normalized_column = func.lower(column)
    accent_map = {'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u', 'â': 'a', 'ê': 'e', 'ô': 'o', 'à': 'a', 'ü': 'u', 'ç': 'c'}
    for accented, unaccented in accent_map.items():
        normalized_column = func.replace(normalized_column, accented, unaccented)
    return func.replace(func.replace(func.replace(func.replace(normalized_column, '.', ''), '-', ''), ',', ''), ' ', '')

def _build_search_query(termo, codigo_produto, montadora, aplicacao_termo, grupo, medidas):
    """Constrói a query de busca de produtos com base nos filtros fornecidos."""
    query = Produto.query

    if termo:
        query = query.join(Aplicacao, Produto.id == Aplicacao.produto_id, isouter=True).distinct()
        for palavra in termo.strip().split():
            palavra_normalizada = _normalize_for_search(palavra)
            if not palavra_normalizada: continue
            query = query.filter(db.or_(
                _apply_db_normalization(Produto.nome).contains(palavra_normalizada),
                _apply_db_normalization(Produto.codigo).contains(palavra_normalizada),
                _apply_db_normalization(Produto.fornecedor).contains(palavra_normalizada),
                _apply_db_normalization(Aplicacao.veiculo).contains(palavra_normalizada),
                _apply_db_normalization(Aplicacao.motor).contains(palavra_normalizada),
                _apply_db_normalization(Produto.conversoes).contains(palavra_normalizada)
            ))

    if codigo_produto:
        codigo_normalizado = _normalize_for_search(codigo_produto)
        query = query.filter(_apply_db_normalization(Produto.codigo).contains(codigo_normalizado))

    if grupo:
        query = query.filter(Produto.grupo.ilike(f"%{grupo}%"))

    if medidas:
        medidas_normalizadas = _normalize_for_search(medidas)
        query = query.filter(_apply_db_normalization(Produto.medidas).contains(medidas_normalizadas))

    needs_join = not termo and (montadora or aplicacao_termo)
    if needs_join:
        query = query.join(Aplicacao, Produto.id == Aplicacao.produto_id)

    if montadora:
        query = query.filter(Aplicacao.montadora.ilike(f"%{montadora}%"))

    if aplicacao_termo:
        aplicacao_like = f'%{aplicacao_termo}%'
        query = query.filter(db.or_(Aplicacao.veiculo.ilike(aplicacao_like), Aplicacao.motor.ilike(aplicacao_like)))
    
    return query

def _download_image_from_url(url: str, upload_folder: str, product_code: str = None) -> str | None:
    """Baixa uma imagem de uma URL e a salva na pasta de uploads."""
    if not url or not url.startswith(('http://', 'https://')):
        return None
    try:
        response = requests.get(url, stream=True, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        response.raise_for_status()

        original_filename = url.split('/')[-1].split('?')[0]
        _, ext = os.path.splitext(original_filename)
        if ext.lower() not in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
            content_type = response.headers.get('content-type')
            ext = '.' + content_type.split('/')[1] if content_type and 'image' in content_type else '.jpg'

        base_name = product_code if product_code else "img"
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S%f')
        filename = secure_filename(f"{base_name}_{timestamp}{ext}")
        
        filepath = os.path.join(upload_folder, filename)
        with open(filepath, 'wb') as f:
            shutil.copyfileobj(response.raw, f)
        return filename
    except requests.exceptions.RequestException as e:
        print(f"Erro ao baixar a imagem da URL {url}: {e}")
        return None

def _atualizar_similares_simetricamente(produto_principal, novos_similares):
    """Atualiza a relação de similares de forma simétrica."""
    similares_antigos = set(produto_principal.similares)
    novos_similares_set = set(novos_similares)

    produto_principal.similares = novos_similares

    for similar_removido in (similares_antigos - novos_similares_set):
        if produto_principal in similar_removido.similares:
            similar_removido.similares.remove(produto_principal)

    for novo_similar in novos_similares:
        if produto_principal not in novo_similar.similares:
            novo_similar.similares.append(produto_principal)

def _get_form_datalists():
    """Busca dados para preencher os datalists nos formulários de produto."""
    grupos_db = db.session.query(Produto.grupo).distinct().filter(Produto.grupo.isnot(None)).order_by(Produto.grupo).all()
    lista_grupos = sorted([g[0] for g in grupos_db])

    fornecedores_db = db.session.query(Produto.fornecedor).distinct().filter(Produto.fornecedor.isnot(None)).order_by(Produto.fornecedor).all()
    lista_fornecedores = sorted([f[0] for f in fornecedores_db])

    montadoras_db = db.session.query(Aplicacao.montadora).distinct().filter(Aplicacao.montadora.isnot(None)).all()
    lista_montadoras_db = [m[0] for m in montadoras_db]
    lista_montadoras_completa = sorted(list(set(lista_montadoras_db + MONTADORAS_PREDEFINIDAS)))

    return {
        "grupos": lista_grupos,
        "fornecedores": lista_fornecedores,
        "montadoras": lista_montadoras_completa
    }

def _parse_year_range(year_str: str | None) -> tuple[int, int]:
    """Converte uma string de ano (ex: "2010", "2010/2015", "2018/...") em uma tupla."""
    if not year_str or not year_str.strip():
        return -1, -1
    year_str = year_str.strip()
    try:
        if year_str.endswith('/...') or year_str.endswith('/'):
            return int(year_str.split('/')[0]), 9999
        if year_str.startswith('.../') or year_str.startswith('/'):
            return 0, int(year_str.split('/')[1])
        if '/' in year_str:
            parts = year_str.split('/')
            return min(int(parts[0]), int(parts[1])), max(int(parts[0]), int(parts[1]))
        return int(year_str), int(year_str)
    except (ValueError, IndexError):
        return -1, -1

def _ranges_overlap(range1: tuple[int, int], range2: tuple[int, int]) -> bool:
    """Verifica se dois intervalos de anos se sobrepõem."""
    return range1[0] <= range2[1] and range2[0] <= range1[1]

def _parse_e_salvar_aplicacoes_novo_formato(produto_alvo: Produto, nome_produto: str, texto_veiculos: str, texto_ano: str, grupo: str = None, fornecedor: str = None):
    """
    Função adaptada para o novo formato do 'produto.csv'.
    Extrai aplicações de strings, lidando com múltiplos veículos e anos.
    """
    produto_alvo.nome = nome_produto
    if grupo: produto_alvo.grupo = grupo
    if fornecedor: produto_alvo.fornecedor = fornecedor

    produto_alvo.aplicacoes.clear()

    if not texto_veiculos:
        return

    texto_completo = f"{texto_veiculos} {texto_ano}"

    for aplicacao_str in texto_completo.split('|'):
        aplicacao_str = aplicacao_str.strip()
        if not aplicacao_str:
            continue

        anos_encontrados = re.findall(r'(\d{4}/\s?\.{3}|\d{4}/\d{4}|\d{4}/\s?\d{4})', aplicacao_str)
        
        veiculos_str = aplicacao_str
        for ano in anos_encontrados:
            veiculos_str = veiculos_str.replace(ano, '')
        
        veiculos = [v.strip() for v in veiculos_str.split(' ') if v.strip()]

        for i, veiculo_completo in enumerate(veiculos):
            ano = anos_encontrados[i] if i < len(anos_encontrados) else (anos_encontrados[0] if anos_encontrados else '')
            
            partes = veiculo_completo.split('-', 1)
            montadora = partes[0].strip().upper() if len(partes) > 1 else None
            nome_veiculo = partes[1].strip() if len(partes) > 1 else veiculo_completo.strip()

            if nome_veiculo:
                nova_aplicacao = Aplicacao(
                    veiculo=nome_veiculo,
                    ano=ano.strip(),
                    montadora=montadora,
                    produto=produto_alvo
                )
                db.session.add(nova_aplicacao)
