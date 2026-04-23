import collections
import io
import json
import os
import shutil
import sqlite3

# --- Gerenciamento de Tarefas em Segundo Plano ---
import subprocess
import sys
import threading
import zipfile
from datetime import datetime

import requests
from flask import (
    Blueprint,
    Response,
    current_app,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    send_file,
    send_from_directory,
    url_for,
)
from flask_login import current_user, login_required, login_user, logout_user
from sqlalchemy import func, or_, text
from sqlalchemy.orm import selectinload
from werkzeug.utils import secure_filename

from app import APP_DATA_PATH, carregar_config_aparencia, db, salvar_config_aparencia
from core_utils import (
    _atualizar_similares_simetricamente,
    _build_search_query,
    _get_form_datalists,
    _parse_year_range,
    _ranges_overlap,
    allowed_file,
    _normalize_for_search,
    _processar_medidas_estruturadas,
    _parsear_medidas_para_dict,
)
from utils.cache_system import invalidate_search_cache
from utils.image_utils import download_image_from_url
from utils.cart_utils import (
    add_to_cart,
    remove_from_cart,
    update_cart_item,
    clear_cart,
    get_cart_items,
    get_cart_count,
    get_cart_summary
)
from models import Aplicacao, ImagemProduto, Produto, User, SugestaoIgnorada, Contato, similares_association

# Importação da função de busca externa (importada separadamente para debugging)
# Importações removidas - busca externa desabilitada
# try:
#     from utils.external_search import buscar_produto_externo
# except ImportError as e:
#     print(f"Erro ao importar busca externa: {e}")
#     def buscar_produto_externo(codigo, marca, timeout=10):
#         return [{"titulo": "Busca externa indisponível", "codigo": codigo, "marca": marca, "descricao": "Módulo de busca externa não carregado", "imagem_url": "", "url": "", "conversoes": [], "fonte": "Sistema"}]
#     def _buscar_produto_externo(codigo, marca, timeout=10):
#         return [{"titulo": "Funcionalidade temporariamente indisponível", "codigo": codigo, "marca": marca, "descricao": "Erro na importação do módulo de busca externa", "imagem_url": "", "url": "", "conversoes": []}]

TASK_STATUS = {"status": "Ocioso", "output": ""}

# --- Criação dos Blueprints ---
main_bp = Blueprint("main", __name__)
auth_bp = Blueprint("auth", __name__)
admin_bp = Blueprint(
    "admin", __name__, url_prefix="/admin"
)  # Rotas de admin terão prefixo /admin

# --- Rotas Principais (main_bp) ---


@main_bp.route("/")
def index():
    """Página inicial que exibe a busca e a lista de montadoras com seus veículos."""
    aplicacoes = (
        db.session.query(Aplicacao.montadora, Aplicacao.veiculo)
        .distinct()
        .filter(Aplicacao.montadora.isnot(None), Aplicacao.montadora != "")
        .order_by(Aplicacao.montadora, Aplicacao.veiculo)
        .all()
    )

    montadoras_com_veiculos = collections.defaultdict(list)
    for montadora, veiculo in aplicacoes:
        montadoras_com_veiculos[montadora.strip().title()].append(veiculo)

    # Prioriza os 4 últimos produtos adicionados que possuam imagens.
    # Cada item terá: url, type ('image'|'video'), filename, produto_id e alt (nome do produto).
    carousel_media = []
    try:
        latest_produtos = (
            Produto.query.filter(Produto.imagens.any())
            .order_by(Produto.id.desc())
            .limit(4)
            .options(selectinload(Produto.imagens))
            .all()
        )
        for produto in latest_produtos:
            if not produto.imagens:
                continue
            imagem = produto.imagens[0]
            fname = imagem.filename
            _, ext = os.path.splitext(fname)
            ext = ext.lower().lstrip(".")
            media_type = "image" if ext in {"png", "jpg", "jpeg", "gif"} else "video"
            media_url = url_for("uploaded_file", filename=fname)
            carousel_media.append(
                {
                    "url": media_url,
                    "type": media_type,
                    "filename": fname,
                    "produto_id": produto.id,
                    "alt": produto.nome,
                }
            )

        # Se não houver produtos com imagens, pode-se manter compatibilidade com uma
        # pasta estática 'uploads/carousel' (fallback) — tentamos só se carousel_media vazia.
        if not carousel_media:
            carousel_dir = os.path.join(APP_DATA_PATH, "uploads", "carousel")

            
            if os.path.exists(carousel_dir):
                allowed = {"png", "jpg", "jpeg", "gif", "mp4", "webm"}
                for fname in sorted(os.listdir(carousel_dir)):
                    if not fname or fname.startswith("."):
                        continue
                    _, ext = os.path.splitext(fname)
                    ext = ext.lower().lstrip(".")
                    if ext in allowed:
                        media_type = "image" if ext in {"png", "jpg", "jpeg", "gif"} else "video"
                        media_url = url_for("uploaded_file", filename=f"carousel/{fname}")
                        carousel_media.append({"url": media_url, "type": media_type, "filename": fname})
    except Exception:
        # Falha ao consultar o banco / listar diretório não deve quebrar a página inicial
        carousel_media = []

    return render_template(
        "index.html",
        montadoras_com_veiculos=dict(sorted(montadoras_com_veiculos.items())),
        show_top_search=False,
        carousel_media=carousel_media,
    )


@main_bp.route("/debug_busca")
def debug_busca():
    """Rota de debug para verificar se o sistema de busca está funcionando"""
    if not current_user.is_authenticated or not (hasattr(current_user, 'eh_admin') and current_user.eh_admin):
        flash("Acesso restrito a administradores", "danger")
        return redirect(url_for('main.index'))
    
    import json
    from datetime import datetime
    
    debug_info = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'status': 'OK'
    }
    
    try:
        # Testa conexão com banco
        total_produtos = Produto.query.count()
        total_aplicacoes = Aplicacao.query.count()
        debug_info['banco'] = {
            'produtos': total_produtos,
            'aplicacoes': total_aplicacoes,
            'status': 'Conectado'
        }
        
        # Testa função de busca
        query_teste = _build_search_query('', '', '', '', '', '')
        resultado_teste = query_teste.limit(1).all()
        debug_info['busca'] = {
            'funcional': True,
            'primeiro_produto': resultado_teste[0].nome if resultado_teste else 'N/A',
            'function_loaded': '_build_search_query carregada'
        }
        
    except Exception as e:
        debug_info['status'] = 'ERRO'
        debug_info['erro'] = str(e)
    
    return f"""
    <html><head><title>Debug Sistema CGI</title></head><body>
    <h1>🔍 Debug Sistema de Busca CGI</h1>
    <pre style="background:#f5f5f5;padding:20px;border-radius:5px;font-family:monospace;">
{json.dumps(debug_info, indent=2, ensure_ascii=False)}
    </pre>
    <p><a href="/">← Voltar à página inicial</a></p>
    </body></html>
    """


@main_bp.route("/buscar")
def buscar():
    """Página de resultados da busca."""
    page = request.args.get("page", 1, type=int)
    termo = request.args.get("termo", "")
    codigo_produto = request.args.get("codigo_produto", "")
    montadora = request.args.get("montadora", "")
    aplicacao_termo = request.args.get("aplicacao", "")
    grupo = request.args.get("grupo", "")
    medidas = request.args.get("medidas", "")
    
    # Novos parâmetros de medidas estruturadas
    largura = request.args.get("largura", "")
    altura = request.args.get("altura", "")
    comprimento = request.args.get("comprimento", "")
    diametro_externo = request.args.get("diametro_externo", "")
    diametro_interno = request.args.get("diametro_interno", "")
    elo = request.args.get("elo", "")
    estrias_internas = request.args.get("estrias_internas", "")
    estrias_externas = request.args.get("estrias_externas", "")
    
    sort_by = request.args.get("sort_by", "codigo")
    sort_dir = request.args.get("sort_dir", "asc")

    PER_PAGE = 20
    query = _build_search_query(
        termo, codigo_produto, montadora, aplicacao_termo, grupo, medidas,
        largura=largura, altura=altura, comprimento=comprimento,
        diametro_externo=diametro_externo, diametro_interno=diametro_interno,
        elo=elo, estrias_internas=estrias_internas, estrias_externas=estrias_externas
    )
    query = query.options(selectinload(Produto.aplicacoes), selectinload(Produto.imagens))

    # Define a coluna de ordenação
    order_column = Produto.codigo
    if sort_by == "nome":
        order_column = Produto.nome

    # Aplica a direção da ordenação
    if sort_dir == "desc":
        query = query.order_by(order_column.desc())
    else:
        query = query.order_by(order_column.asc())

    # Se a busca for por montadora ou aplicação, agrupamos os resultados por veículo.
    # Caso contrário, apenas paginamos a lista de produtos.
    resultados_agrupados = collections.defaultdict(list)
    if montadora or aplicacao_termo:
        # Otimização: Em vez de carregar todos os produtos e depois agrupar na memória,
        # fazemos uma consulta que já traz os dados de forma mais estruturada.
        # A paginação aqui é feita sobre os produtos, não sobre os grupos.
        pagination = query.distinct().paginate(
            page=page, per_page=PER_PAGE, error_out=False
        )
        produtos_paginados = pagination.items

        for produto in produtos_paginados:
            # Filtra as aplicações do produto para mostrar apenas as que batem com a busca
            aplicacoes_relevantes = []
            for app in produto.aplicacoes:
                # Normaliza comparações para ignorar acentos e diferenças de caixa
                monta_ok = True
                if montadora:
                    # Usa comparação exata para evitar matches parciais
                    monta_ok = _normalize_for_search(montadora) == _normalize_for_search(app.montadora or "")

                aplic_ok = True
                if aplicacao_termo:
                    # Usa comparação exata para evitar matches parciais (ex: A1 em A10)
                    aplicacao_normalizada = _normalize_for_search(aplicacao_termo)
                    veiculo_normalizado = _normalize_for_search(app.veiculo or "")
                    motor_normalizado = _normalize_for_search(app.motor or "")
                    
                    aplic_ok = (aplicacao_normalizada == veiculo_normalizado or 
                               aplicacao_normalizada == motor_normalizado)

                if monta_ok and aplic_ok:
                    aplicacoes_relevantes.append(app)
            for aplicacao in aplicacoes_relevantes:
                chave_agrupamento = f"{aplicacao.montadora} {aplicacao.veiculo} {aplicacao.ano or ''}".strip()
                if produto not in resultados_agrupados[chave_agrupamento]:
                    resultados_agrupados[chave_agrupamento].append(produto)
        resultados_agrupados = dict(sorted(resultados_agrupados.items()))
    else:
        # Busca padrão sem agrupamento
        pagination = query.distinct().paginate(
            page=page, per_page=PER_PAGE, error_out=False
        )

    # Prepare search_args for template
    search_args = {
        'termo': termo,
        'codigo_produto': codigo_produto,
        'montadora': montadora,
        'aplicacao': aplicacao_termo,
        'grupo': grupo,
        'medidas': medidas,
        'largura': largura,
        'altura': altura,
        'comprimento': comprimento,
        'diametro_externo': diametro_externo,
        'diametro_interno': diametro_interno,
        'elo': elo,
        'estrias_internas': estrias_internas,
        'estrias_externas': estrias_externas,
        'sort_by': sort_by,
        'sort_dir': sort_dir
    }
    # Remove empty parameters
    search_args = {k: v for k, v in search_args.items() if v}

    return render_template(
        "resultados.html",
        pagination=pagination,
        termo=termo,
        montadora=montadora,
        aplicacao_termo=aplicacao_termo,
        sort_by=sort_by,
        sort_dir=sort_dir,
        resultados_agrupados=resultados_agrupados,
        search_args=search_args,
        is_admin=current_user.is_authenticated and hasattr(current_user, 'eh_admin') and current_user.eh_admin,
        endpoint=request.endpoint,  # Passa o endpoint atual para o template
    )


# Busca por placa removida — rota /api/lookup_plate excluída


@main_bp.route("/peca/<int:id>")
def detalhe_peca(id):
    """Exibe a página de detalhes de um produto específico."""
    
    # Captura contexto da pesquisa para priorizar aplicação
    veiculo_context = request.args.get("veiculo_context", "")
    montadora_context = request.args.get("montadora_context", "")
    
    produto = (
        db.session.query(Produto)
        .options(
            selectinload(Produto.aplicacoes),
            selectinload(Produto.imagens),
            selectinload(Produto.similares).selectinload(
                Produto.aplicacoes
            ),  # Carrega aplicações dos similares
            selectinload(Produto.similares).selectinload(
                Produto.imagens
            ),  # Carrega imagens dos similares
            selectinload(Produto.similar_to),
        )
        .get(id)
    )
    if not produto:
        flash("Produto não encontrado.", "danger")
        return redirect(url_for("main.index"))

    # Registra visualização no histórico de favoritos (se usuário autenticado)
    if current_user.is_authenticated:
        try:
            from routes_favoritos import registrar_visualizacao
            registrar_visualizacao(produto.id, origem='web')
        except Exception as e:
            # Log error silently but don't break page
            current_app.logger.warning(f"Erro ao registrar visualização: {str(e)}")

    aplicacoes_agrupadas = collections.defaultdict(list)
    
    # Função de ordenação que prioriza o veículo pesquisado
    def prioridade_aplicacao(app):
        # Normaliza para comparação (sem acentos, minúsculas)
        veiculo_app = _normalize_for_search(app.veiculo or "")
        montadora_app = _normalize_for_search(app.montadora or "")
        
        # Contexto normalizado da pesquisa
        veiculo_pesquisado = _normalize_for_search(veiculo_context)
        montadora_pesquisada = _normalize_for_search(montadora_context)
        
        # Verificação por contém (não exata): 'gol' bate 'vw gol', 'gol 1.0', etc.
        def _match(termo, campo):
            return bool(termo) and bool(campo) and (termo in campo or campo in termo)

        veic_match = _match(veiculo_pesquisado, veiculo_app)
        monta_match = _match(montadora_pesquisada, montadora_app)

        # Peso de prioridade (menor = maior prioridade)
        if veic_match and monta_match:
            peso_prioridade = 0
        elif veic_match:
            peso_prioridade = 1
        elif monta_match:
            peso_prioridade = 2
        else:
            peso_prioridade = 3
            
        # Retorna tupla: (peso_prioridade, montadora_ordenacao, veiculo_ordenacao)
        return (peso_prioridade, app.montadora or "ZZZ", app.veiculo or "")
    
    sorted_aplicacoes = sorted(produto.aplicacoes, key=prioridade_aplicacao)
    
    for aplicacao in sorted_aplicacoes:
        montadora_chave = aplicacao.montadora or "Sem Montadora"
        aplicacoes_agrupadas[montadora_chave].append(aplicacao)

    # Lógica para encontrar produtos sugeridos
    sugestoes_similares_dict = {}
    ids_ja_relacionados = (
        {p.id for p in produto.similares}
        | {p.id for p in produto.similar_to}
        | {produto.id}
    )

    # Carrega sugestões ignoradas para este produto e evita listá-las
    ignored_rows = (
        db.session.query(SugestaoIgnorada.sugestao_id)
        .filter(SugestaoIgnorada.produto_id == produto.id)
        .all()
    )
    ignored_ids = {r[0] for r in ignored_rows} if ignored_rows else set()

    codigos_conversao = [
        c.strip() for c in (produto.conversoes or "").split(",") if c.strip()
    ]
    if codigos_conversao:
        sugestoes_por_conversao = (
            Produto.query.filter(
                Produto.id.notin_(ids_ja_relacionados),
                Produto.codigo.in_(codigos_conversao),
                Produto.id.notin_(ignored_ids) if ignored_ids else True,
            )
            .options(selectinload(Produto.aplicacoes), selectinload(Produto.imagens))
            .all()
        )
        for p in sugestoes_por_conversao:
            sugestoes_similares_dict[p.id] = p

    sugestoes_por_codigo_produto = (
        Produto.query.filter(
            Produto.id.notin_(ids_ja_relacionados),
            Produto.conversoes.ilike(f"%{produto.codigo}%"),
            Produto.id.notin_(ignored_ids) if ignored_ids else True,
        )
        .options(selectinload(Produto.aplicacoes), selectinload(Produto.imagens))
        .all()
    )
    for p in sugestoes_por_codigo_produto:
        sugestoes_similares_dict[p.id] = p

    # Otimização: Em vez de fazer uma query por aplicação, fazemos uma única query
    # para todos os veículos relevantes e depois filtramos em Python.
    if produto.grupo and produto.aplicacoes:
        # 1. Coleta todos os veículos e seus intervalos de ano do produto principal
        veiculos_principais = {
            app.veiculo: _parse_year_range(app.ano)
            for app in produto.aplicacoes
            if app.veiculo and _parse_year_range(app.ano) != (-1, -1)
        }

        if veiculos_principais:
            # 2. Busca todos os candidatos de uma só vez
            candidatos_gerais = (
                Produto.query
                .filter(
                    Produto.id.notin_(ids_ja_relacionados | set(sugestoes_similares_dict.keys())),
                    Produto.grupo == produto.grupo,
                    Produto.aplicacoes.any(Aplicacao.veiculo.in_(veiculos_principais.keys())),
                    Produto.id.notin_(ignored_ids) if ignored_ids else True
                ).options(
                    selectinload(Produto.aplicacoes),
                    selectinload(Produto.imagens)
                ).all()
            )

            # 3. Processa os candidatos em memória para verificar a sobreposição de anos
            for candidato in candidatos_gerais:
                for app_candidata in candidato.aplicacoes:
                    # Verifica se o veículo do candidato está na lista de veículos do produto principal
                    if app_candidata.veiculo in veiculos_principais:
                        range_principal = veiculos_principais[app_candidata.veiculo]
                        range_candidato = _parse_year_range(app_candidata.ano)
                        if range_candidato != (-1, -1) and _ranges_overlap(range_principal, range_candidato):
                            sugestoes_similares_dict[candidato.id] = candidato
                            break  # Adiciona o candidato uma vez e vai para o próximo

    sugestoes_similares = list(sugestoes_similares_dict.values())

    voltar_url = request.referrer or url_for("main.index")
    ignore_referrer = [
        "/login",
        "/adicionar_peca",
        "/editar",
        "/configuracoes",
        "/gerenciar_usuarios",
    ]
    if any(x in voltar_url for x in ignore_referrer):
        # Se veio de uma página administrativa, voltar para a busca com os argumentos preservados
        # é mais útil do que voltar para o index.
        search_args = request.args.copy()
        search_args.pop(
            "page", None
        )  # Remove a página para voltar à primeira página da busca
        voltar_url = url_for("main.buscar", **search_args)

    return render_template(
        "detalhe_peca.html",
        produto=produto,
        aplicacoes_agrupadas=aplicacoes_agrupadas,
        sugestoes_similares=sugestoes_similares,
        voltar_url=voltar_url,
        veiculo_context=veiculo_context,
        montadora_context=montadora_context,
    )


# --- Rotas de Autenticação (auth_bp) ---


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:  # type: ignore
        return redirect(url_for("main.index"))
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = User.query.filter_by(username=username).first()
        if user is None or not user.check_password(password):
            flash("Usuário ou senha inválidos.", "danger")
            return redirect(url_for("auth.login"))
        login_user(user, remember=True)
        return redirect(url_for("main.index"))
    return render_template("login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("main.index"))


# --- Rotas de Administração (admin_bp) ---


@admin_bp.before_request
@login_required
def require_admin():
    """Garante que todas as rotas neste blueprint sejam acessadas apenas por admins."""
    if not current_user.is_admin:  # type: ignore
        flash(
            "Acesso não autorizado. Apenas administradores podem acessar esta área.",
            "danger",
        )
        return redirect(url_for("main.index"))


@admin_bp.route("/peca/adicionar", methods=["GET", "POST"])
def adicionar_peca():
    if request.method == "POST":
        nome = request.form.get("nome", "").strip().upper()
        codigo = request.form.get("codigo", "").strip().upper()
        fornecedor = request.form.get("fornecedor", "").strip().upper()
        if not nome or not codigo:
            flash("Nome da Peça e Código são campos obrigatórios.", "danger")
            return redirect(url_for("admin.adicionar_peca"))

        # Permite códigos duplicados desde que sejam de fornecedores diferentes
        existente_mesmo_fornecedor = Produto.query.filter(
            func.upper(Produto.codigo) == codigo,
            func.upper(Produto.fornecedor) == fornecedor,
        ).first()
        if existente_mesmo_fornecedor:
            flash(
                f'O código "{codigo}" já está em uso para o fornecedor "{fornecedor}". Por favor, escolha outro.',
                "danger",
            )
            return redirect(url_for("admin.adicionar_peca"))

        try:
            # Processa os campos de medidas estruturados
            medidas_formatadas = _processar_medidas_estruturadas(request.form)
            
            novo_produto = Produto(
                nome=nome,
                codigo=codigo,
                grupo=request.form.get("grupo", "").strip().upper(),
                fornecedor=request.form.get("fornecedor", "").strip().upper(),
                conversoes=request.form.get("conversoes", "").strip().upper(),
                medidas=medidas_formatadas,
                observacoes=request.form.get("observacoes", "").strip().upper(),
            )
            db.session.add(novo_produto)
            db.session.flush()

            # Lógica de upload e download de imagens
            # A rota 'uploaded_file' está no app principal, não em um blueprint.
            # O caminho para salvar o arquivo deve ser o caminho do sistema, não uma URL.
            proxima_ordem = 0
            files = request.files.getlist("imagens")
            for file in files:
                if file and file.filename != "" and allowed_file(file.filename):
                    _, ext = os.path.splitext(file.filename)
                    timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
                    imagem_filename = secure_filename(
                        f"{novo_produto.codigo}_{timestamp}{ext}"
                    )
                    file.save(os.path.join(APP_DATA_PATH, "uploads", imagem_filename))
                    nova_imagem = ImagemProduto(
                        filename=imagem_filename, ordem=proxima_ordem
                    )
                    novo_produto.imagens.append(nova_imagem)
                    proxima_ordem += 1

            for url_field in ("imagem_url", "imagem_url_2", "imagem_url_3"):
                imagem_url = request.form.get(url_field)
                if imagem_url:
                    downloaded_filename = download_image_from_url(
                        imagem_url,
                        os.path.join(APP_DATA_PATH, "uploads"),
                        product_code=novo_produto.codigo,
                    )
                    if downloaded_filename:
                        nova_imagem = ImagemProduto(
                            filename=downloaded_filename, ordem=proxima_ordem
                        )
                        novo_produto.imagens.append(nova_imagem)
                        proxima_ordem += 1

            # Lógica de similares
            similares_ids = [
                int(id)
                for id in request.form.get("similares_ids", "").split(",")
                if id.isdigit()
            ]
            produtos_similares = (
                Produto.query.filter(Produto.id.in_(similares_ids)).all()
                if similares_ids
                else []
            )
            _atualizar_similares_simetricamente(novo_produto, produtos_similares)

            # Processa aplicações
            aplicacoes_form = {}
            for key, value in request.form.items():
                if key.startswith("aplicacoes-"):
                    parts = key.split("-")
                    index, field = parts[1], parts[2]
                    aplicacoes_form.setdefault(index, {})[field] = value.strip().upper()

            for data in aplicacoes_form.values():
                if data.get("veiculo"):
                    # Nunca envie 'id' ao criar uma nova Aplicacao
                    filtered = {k: v for k, v in data.items() if k != "id"}
                    db.session.add(Aplicacao(produto=novo_produto, **filtered))

            db.session.commit()
            invalidate_search_cache()
            flash("Produto adicionado com sucesso!", "success")
            return redirect(url_for("main.detalhe_peca", id=novo_produto.id))
        except Exception as e:
            db.session.rollback()
            flash(f"Ocorreu um erro inesperado ao adicionar o produto: {e}", "danger")

    datalists = _get_form_datalists(app_context=current_app)
    return render_template("adicionar_peca.html", **datalists)


@admin_bp.route("/peca/<int:id>/editar", methods=["GET", "POST"])
def editar_peca(id):
    produto = (
        db.session.query(Produto)
        .options(
            selectinload(Produto.aplicacoes),
            selectinload(Produto.imagens),
            selectinload(Produto.similares),
        )
        .get(id)
    )
    if not produto:
        flash("Produto não encontrado.", "danger")
        return redirect(url_for("main.index"))

    voltar_url = request.referrer or url_for("main.detalhe_peca", id=id)

    if request.method == "POST":
        nome = request.form.get("nome", "").strip().upper()
        codigo = request.form.get("codigo", "").strip().upper()
        fornecedor = request.form.get("fornecedor", "").strip().upper()
        if not nome or not codigo:
            flash("Nome da Peça e Código são campos obrigatórios.", "danger")
            return redirect(url_for("admin.editar_peca", id=id))

        produto_existente = Produto.query.filter(
            func.upper(Produto.codigo) == codigo,
            func.upper(Produto.fornecedor) == fornecedor,
            Produto.id != id,
        ).first()
        if produto_existente:
            flash(
                f'O código "{codigo}" já está em uso para o fornecedor "{fornecedor}" pelo produto "{produto_existente.nome}".',
                "danger",
            )
            return redirect(url_for("admin.editar_peca", id=id))

        try:
            # Processa os campos de medidas estruturados
            medidas_formatadas = _processar_medidas_estruturadas(request.form)
            
            produto.nome = nome
            produto.codigo = codigo
            produto.grupo = request.form.get("grupo", "").strip().upper()
            produto.fornecedor = request.form.get("fornecedor", "").strip().upper()
            produto.conversoes = request.form.get("conversoes", "").strip().upper()
            produto.medidas = medidas_formatadas
            produto.observacoes = request.form.get("observacoes", "").strip().upper()

            similares_ids = [
                int(id)
                for id in request.form.get("similares_ids", "").split(",")
                if id.isdigit()
            ]
            produtos_similares = (
                Produto.query.filter(Produto.id.in_(similares_ids)).all()
                if similares_ids
                else []
            )
            _atualizar_similares_simetricamente(produto, produtos_similares)

            aplicacoes_form = {}
            for key, value in request.form.items():
                if key.startswith("aplicacoes-"):
                    parts = key.split("-")
                    index, field = parts[1], parts[2]
                    aplicacoes_form.setdefault(index, {})[field] = value.strip().upper()

            aplicacoes_existentes_map = {
                str(app.id): app for app in produto.aplicacoes if app.id
            }
            ids_aplicacoes_no_form = {
                data.get("id") for data in aplicacoes_form.values() if data.get("id")
            }

            for data in aplicacoes_form.values():
                if not data.get("veiculo"):
                    continue
                app_id = data.get("id")
                if app_id and app_id in aplicacoes_existentes_map:
                    aplicacao = aplicacoes_existentes_map[app_id]
                    for field, value in data.items():
                        if field != "id":
                            setattr(aplicacao, field, value)
                elif data.get("veiculo"):
                    # Nunca envie 'id' ao criar uma nova Aplicacao
                    filtered_new = {k: v for k, v in data.items() if k != "id"}
                    db.session.add(Aplicacao(produto=produto, **filtered_new))

            ids_para_remover = (
                set(aplicacoes_existentes_map.keys()) - ids_aplicacoes_no_form
            )
            for app_id in ids_para_remover:
                db.session.delete(aplicacoes_existentes_map[app_id])

            proxima_ordem = max([img.ordem for img in produto.imagens] + [-1]) + 1
            files = request.files.getlist("imagens")
            for file in files:
                if file and file.filename != "" and allowed_file(file.filename):
                    _, ext = os.path.splitext(file.filename)
                    timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
                    imagem_filename = secure_filename(
                        f"{produto.codigo}_{timestamp}{ext}"
                    )
                    file.save(os.path.join(APP_DATA_PATH, "uploads", imagem_filename))
                    nova_imagem = ImagemProduto(
                        filename=imagem_filename, ordem=proxima_ordem
                    )
                    produto.imagens.append(nova_imagem)
                    proxima_ordem += 1

            for url_field in ("imagem_url", "imagem_url_2", "imagem_url_3"):
                imagem_url = request.form.get(url_field)
                if imagem_url:
                    downloaded_filename = download_image_from_url(
                        imagem_url,
                        os.path.join(APP_DATA_PATH, "uploads"),
                        product_code=produto.codigo,
                    )
                    if downloaded_filename:
                        nova_imagem = ImagemProduto(
                            filename=downloaded_filename, ordem=proxima_ordem
                        )
                        produto.imagens.append(nova_imagem)
                        proxima_ordem += 1

            ordem_imagens_str = request.form.get("ordem_imagens")
            if ordem_imagens_str:
                ordem_ids = ordem_imagens_str.split(",")
                imagens_existentes_map = {
                    str(img.id): img for img in produto.imagens if img.id is not None
                }
                for i, img_id in enumerate(ordem_ids):
                    if img_id in imagens_existentes_map:
                        imagens_existentes_map[img_id].ordem = i

                novas_imagens = [img for img in produto.imagens if img.id is None]
                for i, nova_img in enumerate(novas_imagens, start=len(ordem_ids)):
                    nova_img.ordem = i

            db.session.commit()
            invalidate_search_cache()
            flash("Produto atualizado com sucesso!", "success")
            return redirect(url_for("main.detalhe_peca", id=produto.id))
        except Exception as e:
            db.session.rollback()
            flash(f"Ocorreu um erro inesperado ao atualizar o produto: {e}", "danger")

    datalists = _get_form_datalists(app_context=current_app)
    medidas_dict = _parsear_medidas_para_dict(produto.medidas)
    return render_template(
        "editar_peca.html", produto=produto, voltar_url=voltar_url, 
        medidas_dict=medidas_dict, **datalists
    )


@admin_bp.route("/peca/<int:id>/clonar", methods=["GET"])
def clonar_peca(id):
    produto_original = (
        db.session.query(Produto)
        .options(
            db.joinedload(Produto.imagens),
            db.joinedload(Produto.aplicacoes),
            db.joinedload(Produto.similares),
        )
        .filter_by(id=id)
        .one_or_none()
    )

    if not produto_original:
        flash("Produto original não encontrado.", "danger")
        return redirect(url_for("main.index"))

    clone_suffix = f"CLONE-{datetime.now().strftime('%H%M%S')}"
    novo_produto = Produto(
        nome=produto_original.nome,
        codigo=f"{produto_original.codigo}-{clone_suffix}",
        grupo=produto_original.grupo,
        fornecedor=produto_original.fornecedor,
        conversoes=produto_original.conversoes,
        medidas=produto_original.medidas,
        observacoes=produto_original.observacoes,
    )

    for imagem_original in produto_original.imagens:
        novo_produto.imagens.append(
            ImagemProduto(
                filename=imagem_original.filename, ordem=imagem_original.ordem
            )
        )

    novo_produto.similares = list(produto_original.similares)

    for aplicacao_original in produto_original.aplicacoes:
        db.session.add(
            Aplicacao(
                produto=novo_produto,
                **{
                    c.name: getattr(aplicacao_original, c.name)
                    for c in aplicacao_original.__table__.columns
                    if c.name not in ["id", "produto_id"]
                },
            )
        )

    db.session.add(novo_produto)
    db.session.commit()
    invalidate_search_cache()

    flash(
        "Produto clonado com sucesso! Por favor, revise o código e os outros dados.",
        "success",
    )
    return redirect(url_for("admin.editar_peca", id=novo_produto.id))


@admin_bp.route("/peca/<int:id>/excluir", methods=["POST"])
def excluir_peca(id):
    produto = (
        db.session.query(Produto)
        .options(db.joinedload(Produto.imagens))
        .filter_by(id=id)
        .one_or_none()
    )
    if not produto:
        flash("Produto não encontrado.", "danger")
        return redirect(url_for("main.index"))

    if produto.imagens:
        filenames_to_check = {img.filename for img in produto.imagens}
        filenames_in_use_elsewhere = {
            res[0]
            for res in db.session.query(ImagemProduto.filename)
            .filter(
                ImagemProduto.filename.in_(filenames_to_check),
                ImagemProduto.produto_id != produto.id,
            )
            .distinct()
        }
        files_to_delete = filenames_to_check - filenames_in_use_elsewhere
        for filename in files_to_delete:
            try:
                os.remove(os.path.join(APP_DATA_PATH, "uploads", filename))
            except OSError as e:
                print(f"Erro ao tentar remover o arquivo de imagem {filename}: {e}")

    try:
        # Remove referências que não possuem cascade explícito no schema.
        db.session.query(SugestaoIgnorada).filter(
            or_(
                SugestaoIgnorada.produto_id == produto.id,
                SugestaoIgnorada.sugestao_id == produto.id,
            )
        ).delete(synchronize_session=False)

        # Limpa tabelas de favoritos/recomendação que referenciam produto_id sem cascade.
        db.session.execute(
            text("DELETE FROM historico_visualizacao WHERE produto_id = :produto_id"),
            {"produto_id": produto.id},
        )
        db.session.execute(
            text("DELETE FROM produto_recomendado WHERE produto_id = :produto_id"),
            {"produto_id": produto.id},
        )
        db.session.execute(
            text("DELETE FROM item_lista_favoritos WHERE produto_id = :produto_id"),
            {"produto_id": produto.id},
        )

        db.session.execute(
            similares_association.delete().where(
                or_(
                    similares_association.c.produto_id == produto.id,
                    similares_association.c.similar_id == produto.id,
                )
            )
        )

        db.session.delete(produto)
        db.session.commit()
        invalidate_search_cache()

        flash("Produto excluído com sucesso.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Erro ao excluir produto: {e}", "danger")

    return redirect(url_for("main.index"))


@admin_bp.route("/peca/<int:produto_id>/similar/<int:similar_id>/remover", methods=["POST", "DELETE"])
def remover_similar(produto_id, similar_id):
    """Remove a relação de similaridade entre dois produtos de forma simétrica.

    Suporta POST (form) e DELETE (AJAX). Retorna JSON em caso de DELETE, ou
    faz redirect de volta para a página de detalhe em caso de POST.
    """
    produto = db.session.get(Produto, produto_id)
    similar = db.session.get(Produto, similar_id)

    if not produto or not similar:
        if request.method == "DELETE":
            return {"success": False, "message": "Produto não encontrado."}, 404
        flash("Produto não encontrado.", "danger")
        return redirect(request.referrer or url_for("main.index"))

    try:
        # Remove a relação simétrica se existir
        if similar in produto.similares:
            produto.similares.remove(similar)
        if produto in similar.similares:
            similar.similares.remove(produto)

        db.session.commit()
        invalidate_search_cache()

        if request.method == "DELETE":
            return {"success": True, "message": "Similar removido com sucesso."}

        flash("Similar removido com sucesso.", "success")
        return redirect(url_for("main.detalhe_peca", id=produto.id))

    except Exception as e:
        db.session.rollback()
        if request.method == "DELETE":
            return {"success": False, "message": f"Erro no servidor: {e}"}, 500
        flash(f"Erro ao remover similar: {e}", "danger")
        return redirect(request.referrer or url_for("main.detalhe_peca", id=produto.id))


@admin_bp.route("/imagem/<int:id>/excluir", methods=["POST", "DELETE"])
def excluir_imagem(id):
    imagem = db.session.get(ImagemProduto, id)
    if not imagem:
        return (
            ({"success": False, "message": "Imagem não encontrada"}, 404)
            if request.method == "DELETE"
            else redirect(request.referrer or url_for("main.index"))
        )

    produto_id = imagem.produto_id
    filename = imagem.filename
    db.session.delete(imagem)
    db.session.commit()
    invalidate_search_cache()

    if ImagemProduto.query.filter_by(filename=filename).count() == 0:
        filepath = os.path.join(APP_DATA_PATH, "uploads", filename)
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except OSError as e:
                print(f"Erro ao tentar remover o arquivo de imagem {filename}: {e}")

    if request.method == "DELETE":
        return {"success": True, "message": "Imagem excluída com sucesso."}
    else:
        flash("Imagem excluída com sucesso.", "success")
        return redirect(url_for("admin.editar_peca", id=produto_id))


@admin_bp.route("/aplicacao/<int:id>/excluir_ajax", methods=["DELETE"])
def excluir_aplicacao_ajax(id):
    """Exclui uma aplicação via AJAX e retorna uma resposta JSON."""
    aplicacao = db.session.get(Aplicacao, id)
    if not aplicacao:
        return {"success": False, "message": "Aplicação não encontrada"}, 404

    try:
        db.session.delete(aplicacao)
        db.session.commit()
        return {"success": True, "message": "Aplicação excluída com sucesso"}

    except Exception as e:
        db.session.rollback()
        print(f"Erro ao excluir aplicação: {e}")
        return {"success": False, "message": "Erro no servidor"}, 500


@admin_bp.route("/aplicacao/adicionar", methods=["GET", "POST"])
def adicionar_aplicacao():
    # Espera produto_id em query string ou form
    produto_id = request.values.get("produto_id", type=int)
    produto = db.session.get(Produto, produto_id) if produto_id else None
    if request.method == "POST":
        veiculo = request.form.get("veiculo", "").strip().upper()
        ano = request.form.get("ano", "").strip().upper()
        motor = request.form.get("motor", "").strip().upper()
        conf_mtr = request.form.get("conf_mtr", "").strip().upper()
        montadora = request.form.get("montadora", "").strip().upper()
        if not produto:
            flash("Produto não encontrado para adicionar aplicação.", "danger")
            return redirect(url_for("main.index"))
        if not veiculo:
            flash("Veículo é obrigatório.", "danger")
            return redirect(
                url_for("admin.gerenciar_aplicacoes", produto_id=produto.id)
            )
        nova = Aplicacao(
            produto=produto,
            veiculo=veiculo,
            ano=ano,
            motor=motor,
            conf_mtr=conf_mtr,
            montadora=montadora,
        )
        db.session.add(nova)
        db.session.commit()
        flash("Aplicação adicionada com sucesso.", "success")
        return redirect(url_for("main.detalhe_peca", id=produto.id))

    # GET: renderiza o formulário mínimo
    return render_template("adicionar_aplicacao.html", produto=produto)


@admin_bp.route("/aplicacao/<int:id>/editar", methods=["GET", "POST"])
def editar_aplicacao(id):
    aplicacao = db.session.get(Aplicacao, id)
    if not aplicacao:
        flash("Aplicação não encontrada.", "danger")
        return redirect(url_for("main.index"))

    if request.method == "POST":
        aplicacao.veiculo = request.form.get("veiculo", "").strip().upper()
        aplicacao.ano = request.form.get("ano", "").strip().upper()
        aplicacao.motor = request.form.get("motor", "").strip().upper()
        aplicacao.conf_mtr = request.form.get("conf_mtr", "").strip().upper()
        db.session.commit()
        flash("Aplicação atualizada com sucesso.", "success")
        return redirect(url_for("main.detalhe_peca", id=aplicacao.produto_id))

    return render_template("editar_aplicacao.html", aplicacao=aplicacao)


@admin_bp.route("/aplicacoes/<int:produto_id>", methods=["GET", "POST"])
def gerenciar_aplicacoes(produto_id):
    produto = db.session.get(Produto, produto_id)
    if not produto:
        flash("Produto não encontrado.", "danger")
        return redirect(url_for("main.index"))

    if request.method == "POST":
        veiculo = request.form.get("veiculo", "").strip().upper()
        ano = request.form.get("ano", "").strip().upper()
        motor = request.form.get("motor", "").strip().upper()
        conf_mtr = request.form.get("conf_mtr", "").strip().upper()
        if not veiculo:
            flash("Veículo é obrigatório para a aplicação.", "danger")
            return redirect(
                url_for("admin.gerenciar_aplicacoes", produto_id=produto.id)
            )
        nova = Aplicacao(
            produto=produto, veiculo=veiculo, ano=ano, motor=motor, conf_mtr=conf_mtr
        )
        db.session.add(nova)
        db.session.commit()
        flash("Aplicação adicionada com sucesso.", "success")
        return redirect(url_for("admin.gerenciar_aplicacoes", produto_id=produto.id))

    return render_template("gerenciar_aplicacoes.html", produto=produto)


@admin_bp.route("/aplicacao/<int:id>/excluir", methods=["POST"])
def excluir_aplicacao(id):
    aplicacao = db.session.get(Aplicacao, id)
    if not aplicacao:
        flash("Aplicação não encontrada.", "danger")
        return redirect(url_for("main.index"))
    produto_id = aplicacao.produto_id
    try:
        db.session.delete(aplicacao)
        db.session.commit()
        flash("Aplicação excluída com sucesso.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Erro ao excluir aplicação: {e}", "danger")
    return redirect(url_for("admin.gerenciar_aplicacoes", produto_id=produto_id))


@admin_bp.route("/gerenciar_usuarios")
def gerenciar_usuarios():
    _repair_null_user_ids()
    usuarios = User.query.filter(User.id.isnot(None)).order_by(User.id).all()
    return render_template("gerenciar_usuarios.html", usuarios=usuarios)


def _repair_null_user_ids():
    """Corrige IDs nulos de usuários em bancos legados mal migrados.

    Em algumas bases antigas, a coluna `user.id` ficou sem PK/auto incremento,
    permitindo inserções com `id` nulo. Isso quebra templates/rotas que dependem
    de `user.id`. Esta rotina atribui IDs sequenciais para registros nulos.
    """
    with db.engine.begin() as connection:
        missing_rows = connection.execute(
            text('SELECT rowid FROM "user" WHERE id IS NULL ORDER BY rowid')
        ).fetchall()

        if not missing_rows:
            return

        max_id = connection.execute(
            text('SELECT COALESCE(MAX(id), 0) FROM "user"')
        ).scalar() or 0

        for row in missing_rows:
            max_id += 1
            connection.execute(
                text('UPDATE "user" SET id = :new_id WHERE rowid = :row_id'),
                {"new_id": max_id, "row_id": row[0]},
            )


@admin_bp.route("/adicionar_usuario", methods=["POST"])
def adicionar_usuario():
    _repair_null_user_ids()
    username = (request.form.get("username") or "").strip()
    password = request.form.get("password") or ""

    if not username or not password:
        flash("Nome de usuário e senha são obrigatórios.", "danger")
        return redirect(url_for("admin.gerenciar_usuarios"))

    if User.query.filter_by(username=username).first():
        flash(f'O nome de usuário "{username}" já existe.', "danger")
    else:
        next_user_id = (db.session.query(func.max(User.id)).scalar() or 0) + 1
        new_user = User(
            id=next_user_id,
            username=username,
            is_admin=request.form.get("is_admin") == "on",
        )
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        flash(f'Usuário "{username}" criado com sucesso!', "success")

    return redirect(url_for("admin.gerenciar_usuarios"))


@admin_bp.route("/excluir_usuario/<int:user_id>", methods=["POST"])
def excluir_usuario(user_id):
    user_to_delete = db.session.get(User, user_id)
    if user_to_delete and user_to_delete.id != current_user.id and user_to_delete.username != "admin":  # type: ignore
        db.session.delete(user_to_delete)
        db.session.commit()
        flash(f'Usuário "{user_to_delete.username}" excluído com sucesso.', "success")
    else:
        flash(
            "Não é possível excluir este usuário (você mesmo, ou o admin principal).",
            "danger",
        )
    return redirect(url_for("admin.gerenciar_usuarios"))


@admin_bp.route("/mudar_senha_usuario/<int:user_id>", methods=["POST"])
def mudar_senha_usuario(user_id):
    user_to_update = db.session.get(User, user_id)
    new_password = request.form.get("new_password")
    if user_to_update and new_password:
        user_to_update.set_password(new_password)
        db.session.commit()
        flash(
            f'Senha do usuário "{user_to_update.username}" alterada com sucesso.',
            "success",
        )
    else:
        flash("Não foi possível alterar a senha.", "danger")
    return redirect(url_for("admin.gerenciar_usuarios"))


@admin_bp.route("/configuracoes", methods=["GET", "POST"])
def configuracoes():
    config = carregar_config_aparencia()

    if request.method == "POST":
        # Cor principal
        config["cor_principal"] = request.form.get("cor_principal", "#ff6600")
        # Cores das colunas em Detalhes do Produto
        config["cor_coluna_conversoes"] = request.form.get("cor_coluna_conversoes", config.get("cor_coluna_conversoes", "#fff3cd"))
        config["cor_coluna_medidas"] = request.form.get("cor_coluna_medidas", config.get("cor_coluna_medidas", "#d1ecf1"))
        
        # Configurações de plano de fundo
        config["background_tipo"] = request.form.get("background_tipo", "cor")
        config["background_cor"] = request.form.get("background_cor", "#ffffff")
        config["background_repeat"] = request.form.get("background_repeat", "no-repeat")
        config["background_position"] = request.form.get("background_position", "center center")
        config["background_size"] = request.form.get("background_size", "cover")
        
        # Opacidade do plano de fundo
        try:
            opacity = float(request.form.get("background_opacity", 1.0))
            config["background_opacity"] = max(0.0, min(1.0, opacity))
        except (ValueError, TypeError):
            config["background_opacity"] = 1.0
        
        # Pesquisa externa desabilitada permanentemente
        config["pesquisa_externa_ativa"] = False

        # Logo principal do sistema
        if "logo" in request.files:
            file = request.files["logo"]
            if file and file.filename != "" and allowed_file(file.filename):
                logo_filename = "logo" + os.path.splitext(file.filename)[1]
                file.save(os.path.join(APP_DATA_PATH, "uploads", logo_filename))
                config["logo_path"] = logo_filename

        # Imagem de plano de fundo
        if "background_imagem" in request.files:
            file = request.files["background_imagem"]
            if file and file.filename != "" and allowed_file(file.filename):
                bg_filename = "background" + os.path.splitext(file.filename)[1]
                file.save(os.path.join(APP_DATA_PATH, "uploads", bg_filename))
                config["background_imagem"] = bg_filename

        # Upload de ícones por montadora (inputs com nome: icon_<slug>)
        # Slug padrão: montadora em minúsculas, espaços -> '-', remover duplos '--'
        updated_icons = config.get("montadora_icons", {})
        for field_name, storage in request.files.items():
            if not field_name.startswith("icon_"):
                continue
            file = storage
            if not file or file.filename == "" or not allowed_file(file.filename):
                continue
            slug = field_name[len("icon_"):].strip().lower()
            # Garante um nome de arquivo consistente: icon_<slug>.<ext>
            _, ext = os.path.splitext(file.filename)
            safe_name = f"icon_{slug}{ext.lower()}"
            file.save(os.path.join(APP_DATA_PATH, "uploads", safe_name))
            updated_icons[slug] = safe_name

        config["montadora_icons"] = updated_icons

        salvar_config_aparencia(config)
        flash("Configurações salvas com sucesso!", "success")
        return redirect(url_for("admin.configuracoes"))

    # Montadoras distintas do banco para exibir na UI
    montadoras = (
        db.session.query(Aplicacao.montadora)
        .distinct()
        .filter(Aplicacao.montadora.isnot(None), Aplicacao.montadora != "")
        .order_by(Aplicacao.montadora)
        .all()
    )
    montadoras = [m[0] for m in montadoras]

    return render_template("configuracoes.html", config=config, montadoras=montadoras)


@admin_bp.route("/configuracoes/restaurar_cores", methods=["POST"])
def restaurar_cores_padrao():
    """Restaura as cores de aparência para os padrões originais do sistema."""
    config = carregar_config_aparencia()
    config["cor_principal"] = "#ff6600"
    config["cor_coluna_conversoes"] = "#fff3cd"
    config["cor_coluna_medidas"] = "#d1ecf1"
    # Restaura configurações de plano de fundo para o padrão
    config["background_tipo"] = "cor"
    config["background_cor"] = "#ffffff"
    config["background_imagem"] = None
    config["background_repeat"] = "no-repeat"
    config["background_position"] = "center center"
    config["background_size"] = "cover"
    config["background_opacity"] = 1.0
    salvar_config_aparencia(config)
    flash("Cores e configurações de aparência restauradas para o padrão com sucesso!", "success")
    return redirect(url_for("admin.configuracoes"))

@admin_bp.route("/catalogo/pdf")
@login_required
def catalogo_pdf():
    """Gera PDF com todo o catálogo de produtos (estilo semelhante ao PDF do carrinho)."""
    if not current_user.is_admin:
        flash('Acesso negado: apenas administradores podem gerar o catálogo.', 'danger')
        return redirect(url_for('admin.configuracoes'))

    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER
    import tempfile
    import time

    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf', prefix='catalogo_')
    temp_path = temp_file.name
    temp_file.close()

    try:
        produtos = Produto.query.options(selectinload(Produto.imagens), selectinload(Produto.aplicacoes)).order_by(Produto.nome).all()

        doc = SimpleDocTemplate(temp_path, pagesize=A4, topMargin=2*cm, bottomMargin=2*cm, leftMargin=2*cm, rightMargin=2*cm)
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=18, textColor=colors.darkblue, alignment=TA_CENTER, spaceAfter=20)
        normal_style = styles['Normal']; normal_style.fontSize = 9
        name_style = ParagraphStyle('NameStyle', parent=normal_style, fontSize=10, leading=12, wordWrap='CJK')
        small_style = ParagraphStyle('SmallCell', parent=normal_style, fontSize=7, leading=8)

        story = []
        story.append(Paragraph('CATÁLOGO DE PEÇAS', title_style))
        story.append(Spacer(1,12))

        import re
        def wrap_and_truncate(text, chunk=20, max_total=800):
            if not text:
                return ''
            t = str(text)
            if len(t) > max_total:
                t = t[:max_total-3] + '...'
            pattern = re.compile(r"(\S{%d})" % chunk)
            return pattern.sub(lambda m: m.group(1) + '\u200b', t)

        table_data = []
        table_data.append([
            Paragraph('<b>Imagem</b>', normal_style),
            Paragraph('<b>Código</b>', normal_style),
            Paragraph('<b>Nome</b>', normal_style),
            Paragraph('<b>Fornecedor</b>', normal_style),
            Paragraph('<b>Ano</b>', normal_style),
            Paragraph('<b>Aplicações</b>', normal_style),
            Paragraph('<b>Motor</b>', normal_style),
        ])

        for produto in produtos:
            img_flowable = ''
            try:
                if produto.imagens:
                    fname = produto.imagens[0].filename
                    uploads_folder = current_app.config.get('UPLOAD_FOLDER')
                    if uploads_folder:
                        img_path = os.path.join(uploads_folder, fname)
                        if os.path.exists(img_path):
                            img_flowable = RLImage(img_path, width=1.8*cm, height=1.8*cm)
            except Exception:
                img_flowable = ''

            code_cell = Paragraph(produto.codigo or '', normal_style)
            name_text = wrap_and_truncate(produto.nome or '', chunk=20, max_total=300)
            name_cell = Paragraph(name_text, name_style)
            supplier_cell = Paragraph(produto.fornecedor or '', normal_style)

            apps_lines = []
            anos_list = []
            motors_list = []
            for aplicacao in produto.aplicacoes:
                parts = []
                if aplicacao.montadora:
                    parts.append(aplicacao.montadora)
                if aplicacao.veiculo:
                    parts.append(aplicacao.veiculo)
                apps_lines.append(' '.join(parts))
                anos_list.append(str(aplicacao.ano).strip() if aplicacao.ano else '')
                motors_list.append(str(aplicacao.motor).strip() if aplicacao.motor else '')

            if not apps_lines:
                apps_lines = ['Não informadas']
            if not anos_list:
                anos_list = ['']
            if not motors_list:
                motors_list = ['']

            app_list = [wrap_and_truncate(a, chunk=25, max_total=800) for a in apps_lines]
            max_rows = max(len(app_list), len(anos_list), len(motors_list))
            for i in range(max_rows):
                year_cell = anos_list[i] if i < len(anos_list) else ''
                motor_cell = motors_list[i] if i < len(motors_list) else ''
                app_cell = app_list[i] if i < len(app_list) else ''

                year_par = Paragraph(year_cell.replace('\n','<br/>'), small_style) if year_cell else Paragraph('', small_style)
                app_par = Paragraph(app_cell.replace('\n','<br/>'), small_style) if app_cell else Paragraph('', small_style)
                motor_par = Paragraph(motor_cell, small_style) if motor_cell else Paragraph('', small_style)

                if i == 0:
                    table_data.append([img_flowable, code_cell, name_cell, supplier_cell, year_par, app_par, motor_par])
                else:
                    table_data.append(['', '', '', '', year_par, app_par, motor_par])

        col_widths = [1.8*cm, 2.5*cm, 5.0*cm, 2.0*cm, 1.6*cm, 2.2*cm, 1.4*cm]
        products_table = Table(table_data, colWidths=col_widths, hAlign='LEFT')
        products_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('GRID', (0, 0), (-1, -1), 0.4, colors.lightgrey),
            ('BACKGROUND', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('LEFTPADDING', (0,0), (-1,-1), 4),
            ('RIGHTPADDING', (0,0), (-1,-1), 4),
        ]))

        story.append(products_table)
        story.append(Spacer(1, 16))

        footer = Paragraph('Documento gerado automaticamente pelo Sistema de Catálogo de Peças', ParagraphStyle('Footer', parent=normal_style, fontSize=8, textColor=colors.grey, alignment=TA_CENTER))
        story.append(footer)

        doc.build(story)

        return send_file(temp_path, as_attachment=True, download_name=f'catalogo_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf', mimetype='application/pdf')

    except Exception as e:
        try:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
        except Exception:
            pass
        flash(f'Erro ao gerar catálogo PDF: {e}', 'danger')
        return redirect(url_for('admin.configuracoes'))


@admin_bp.route("/tarefas", methods=["GET"])
def pagina_tarefas():
    """Exibe a página para executar tarefas de importação e vinculação."""
    return render_template("tarefas.html", task_status=TASK_STATUS)


@admin_bp.route("/tarefas/status", methods=["GET"])
def status_tarefa():
    """Endpoint AJAX para obter o status da tarefa atual."""
    return jsonify(TASK_STATUS)


def _run_task_in_background(command_args, log_file_path):
    """Função genérica para executar um comando CLI em um subprocesso."""
    try:
        # Redireciona a saída padrão e de erro para um arquivo de log (modo binário para evitar problemas de encoding)
        # O processo filho escreverá bytes brutos; ao ler o log, o leitor poderá tentar decodificar com utf-8 e
        # fazer fallback para latin-1 se necessário.
        with open(log_file_path, "wb") as log_file:
            # Encontra o caminho para o executável python do ambiente virtual
            python_executable = sys.executable
            process = subprocess.Popen(
                [python_executable, "run.py"] + command_args,
                stdout=log_file,
                stderr=subprocess.STDOUT,
            )
            process.wait()  # Espera o processo terminar

        # Lê o log para o status final (tenta decodificar em utf-8 com fallback)
        output = ""
        try:
            with open(log_file_path, "rb") as log_file:
                data = log_file.read()
            try:
                output = data.decode("utf-8")
            except Exception:
                output = data.decode("latin-1", errors="replace")
        except Exception as e:
            output = f"(não foi possível ler o arquivo de log: {e})"

        if process.returncode == 0:
            TASK_STATUS["status"] = (
                f"Concluído com sucesso às {datetime.now().strftime('%H:%M:%S')}"
            )
        else:
            TASK_STATUS["status"] = f"Falhou às {datetime.now().strftime('%H:%M:%S')}"

        TASK_STATUS["output"] = output

    except Exception as e:
        TASK_STATUS["status"] = "Erro crítico ao iniciar a tarefa."
        TASK_STATUS["output"] = str(e)


@admin_bp.route("/tarefas/importar_csv", methods=["POST"])
def tarefa_importar_csv():
    global TASK_STATUS
    if TASK_STATUS["status"].startswith("Executando"):
        flash("Uma tarefa já está em execução. Aguarde a sua conclusão.", "warning")
        return redirect(url_for("admin.pagina_tarefas"))

    if "csv_file" not in request.files or request.files["csv_file"].filename == "":
        flash("Nenhum arquivo CSV foi enviado.", "danger")
        return redirect(url_for("admin.pagina_tarefas"))

    file = request.files["csv_file"]
    if not file.filename.endswith(".csv"):
        flash("Arquivo inválido. Por favor, envie um arquivo .csv.", "danger")
        return redirect(url_for("admin.pagina_tarefas"))

    temp_csv_path = os.path.join(
        APP_DATA_PATH,
        secure_filename(f"import_{datetime.now().strftime('%Y%m%d%H%M%S')}.csv"),
    )
    file.save(temp_csv_path)

    TASK_STATUS = {
        "status": "Executando: Importação de CSV...",
        "output": "Iniciando...",
    }
    log_file = os.path.join(APP_DATA_PATH, "task_import.log")
    thread = threading.Thread(
        target=_run_task_in_background, args=(["import-csv", temp_csv_path], log_file)
    )
    thread.start()

    flash("A importação foi iniciada em segundo plano.", "info")
    return redirect(url_for("admin.pagina_tarefas"))


@admin_bp.route("/tarefas/vincular_imagens", methods=["POST"])
def tarefa_vincular_imagens():
    global TASK_STATUS
    if TASK_STATUS["status"].startswith("Executando"):
        flash("Uma tarefa já está em execução. Aguarde a sua conclusão.", "warning")
        return redirect(url_for("admin.pagina_tarefas"))

    TASK_STATUS = {
        "status": "Executando: Vinculação de Imagens...",
        "output": "Iniciando...",
    }
    log_file = os.path.join(APP_DATA_PATH, "task_link_images.log")
    thread = threading.Thread(
        target=_run_task_in_background, args=(["link-images"], log_file)
    )
    thread.start()

    flash("A vinculação de imagens foi iniciada em segundo plano.", "info")
    return redirect(url_for("admin.pagina_tarefas"))


def _verificar_foreign_keys_banco(db_path):
    """Verifica integridade das foreign keys no banco de dados"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Verifica especificamente problemas em compartilhamento_lista
        cursor.execute("""
            SELECT COUNT(*) FROM compartilhamento_lista 
            WHERE compartilhado_por NOT IN (SELECT id FROM user)
            OR compartilhado_com NOT IN (SELECT id FROM user)
        """)
        problemas = cursor.fetchone()[0]
        
        conn.close()
        return problemas == 0, problemas
    except Exception:
        return False, 0

def _corrigir_foreign_keys_automatico(db_path):
    """Correção automática de foreign keys órfãos"""
    try:
        print("[BACKUP] Corrigindo foreign keys órfãos automaticamente...")
        
        # Faz backup antes da correção
        backup_path = f"{db_path}.backup_before_fk_fix"
        import shutil
        shutil.copy2(db_path, backup_path)
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Remove registros órfãos
        cursor.execute("""
            DELETE FROM compartilhamento_lista 
            WHERE compartilhado_por NOT IN (SELECT id FROM user)
            OR compartilhado_com NOT IN (SELECT id FROM user)
        """)
        
        removidos = cursor.rowcount
        conn.commit()
        conn.close()
        
        print(f"[BACKUP] ✓ {removidos} registros órfãos removidos")
        return True
        
    except Exception as e:
        print(f"[BACKUP] ✗ Erro na correção automática: {e}")
        return False

@admin_bp.route("/backup")
@login_required
def backup():
    """Cria um backup completo do banco de dados e arquivos da aplicação."""
    print("[BACKUP] Iniciando processo de backup (streaming em memória)...")
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    backup_filename = f"backup_catalogo_{timestamp}.zip"
    source_db_path = os.path.join(APP_DATA_PATH, "catalogo.db")

    try:
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            # Backup do banco de dados como SQL dump
            if os.path.exists(source_db_path):
                print("[BACKUP] Verificando integridade do banco...")
                
                # Verifica foreign keys antes do backup
                fk_integro, problemas_count = _verificar_foreign_keys_banco(source_db_path)
                
                if not fk_integro:
                    print(f"[BACKUP] ⚠ {problemas_count} problemas de foreign key detectados")
                    
                    # Tenta correção automática
                    if _corrigir_foreign_keys_automatico(source_db_path):
                        print("[BACKUP] ✓ Foreign keys corrigidos automaticamente")
                        flash("Problemas de integridade detectados e corrigidos automaticamente durante o backup.", "info")
                    else:
                        print("[BACKUP] ✗ Falha na correção automática")
                        flash("Problemas de integridade detectados. Backup pode falhar.", "warning")
                
                print("[BACKUP] Fazendo dump do banco de dados...")
                import sqlite3

                try:
                    # Tenta o método normal primeiro
                    bck_conn = sqlite3.connect(":memory:")
                    src_conn = sqlite3.connect(f"file:{source_db_path}?mode=ro", uri=True)
                    src_conn.backup(bck_conn)
                    db_dump = "\n".join(bck_conn.iterdump())
                    zf.writestr("catalogo.db.sql", db_dump)
                    src_conn.close()
                    bck_conn.close()
                    print("[BACKUP] ✓ Dump SQL do banco concluído")
                    
                except sqlite3.OperationalError as e:
                    if "foreign key mismatch" in str(e):
                        print("[BACKUP] ⚠ Erro de foreign key no dump, tentando backup direto do arquivo...")
                        # Se falhar, faz backup direto do arquivo .db
                        zf.write(source_db_path, "catalogo.db")
                        flash("Backup do arquivo de banco criado (SQL dump falhou devido a inconsistências)", "warning")
                        print("[BACKUP] ✓ Backup direto do arquivo .db concluído")
                    else:
                        raise e
                        
            else:
                print(f"[BACKUP] ⚠ Banco de dados não encontrado em: {source_db_path}")

            # Adiciona todos os outros arquivos (uploads, configs, etc)
            file_count = 0
            for root, _, files in os.walk(APP_DATA_PATH):
                for file in files:
                    if file.startswith("catalogo.db"):
                        continue
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, APP_DATA_PATH)
                    zf.write(file_path, arcname)
                    file_count += 1
            
            print(f"[BACKUP] ✓ {file_count} arquivos adicionados ao backup")

        # Prepara buffer para envio
        buf.seek(0)
        print(f"[BACKUP] ✓ Backup preparado em memória: {backup_filename}")
        flash(f"Backup criado com sucesso! Iniciando download: {backup_filename}", "success")
        return send_file(buf, as_attachment=True, download_name=backup_filename, mimetype="application/zip")

    except Exception as e:
        print(f"[BACKUP] ✗ ERRO: {e}")
        import traceback
        traceback.print_exc()
        flash(f"Erro ao criar o backup: {e}", "danger")
        return redirect(url_for("admin.configuracoes"))


@admin_bp.route("/restaurar", methods=["POST"])
def restaurar():
    if "backup_file" not in request.files:
        flash("Nenhum arquivo de backup foi enviado.", "danger")
        return redirect(url_for("admin.configuracoes"))

    file = request.files["backup_file"]
    if file.filename == "" or not file.filename.endswith(".zip"):
        flash("Arquivo inválido. Por favor, envie um arquivo .zip.", "danger")
        return redirect(url_for("admin.configuracoes"))

    restore_filepath = os.path.join(APP_DATA_PATH, "backup_para_restaurar.zip")
    file.save(restore_filepath)

    is_sql_backup = False
    with zipfile.ZipFile(restore_filepath, "r") as zf:
        if "catalogo.db.sql" in zf.namelist():
            is_sql_backup = True

    if is_sql_backup:
        # Evita tentar sobrescrever o banco em tempo de execução (causa
        # "arquivo em uso" no Windows). Em vez disso, grava o zip recebido
        # e solicita um reinício para que a restauração seja feita na
        # inicialização (seguro, pois a app estará parada).
        restart_trigger_file = os.path.join(APP_DATA_PATH, "RESTART_REQUIRED")
        try:
            with open(restart_trigger_file, "w") as f:
                f.write("restart")
        except Exception:
            # Se não conseguir escrever o gatilho, ao menos informe o usuário
            flash(
                "Backup recebido, mas não foi possível agendar a restauração. Pare o servidor manualmente e coloque 'backup_para_restaurar.zip' em APP_DATA_PATH.",
                "warning",
            )
            return redirect(url_for("admin.configuracoes"))

        # Mostra tela de reiniciando (a lógica em run.py irá executar a restauração
        # ao detectar o arquivo 'backup_para_restaurar.zip' durante a inicialização).
        return render_template("reiniciando.html")
    else:
        restart_trigger_file = os.path.join(APP_DATA_PATH, "RESTART_REQUIRED")
        with open(restart_trigger_file, "w") as f:
            f.write("restart")
        return render_template("reiniciando.html")


@admin_bp.route("/exportar/csv")
def exportar_csv():
    # Reutiliza os mesmos parâmetros da busca
    args = request.args.copy()
    query = _build_search_query(
        args.get("termo", ""),
        args.get("codigo_produto", ""),
        args.get("montadora", ""),
        args.get("aplicacao", ""),
        args.get("grupo", ""),
        args.get("medidas", ""),
    )
    resultados = query.options(db.joinedload(Produto.aplicacoes)).all()

    def generate():
        yield "codigo,nome,grupo,fornecedor,conversoes,medidas,observacoes,aplicacoes_json\n"
        for produto in resultados:
            aplicacoes_list = [
                {
                    "veiculo": app.veiculo,
                    "ano": app.ano,
                    "motor": app.motor,
                    "conf_mtr": app.conf_mtr,
                    "montadora": app.montadora,
                }
                for app in produto.aplicacoes
            ]
            aplicacoes_json = json.dumps(aplicacoes_list, ensure_ascii=False)
            row_data = [
                produto.codigo or "",
                produto.nome or "",
                produto.grupo or "",
                produto.fornecedor or "",
                produto.conversoes or "",
                produto.medidas or "",
                produto.observacoes or "",
                aplicacoes_json,
            ]
            # Escapa aspas duplas dentro dos campos e envolve cada campo com aspas
            row = (
                ",".join(
                    [f'"{str(field).replace("\"", "\"\"")}"' for field in row_data]
                )
                + "\n"
            )
            yield row

    return Response(
        generate(),
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=export_pecas.csv"},
    )


# --- Rotas de API (para AJAX) ---


@main_bp.route("/api/check_codigo")
@login_required
def check_codigo():
    """Verifica se um código de produto já existe no banco de dados (via AJAX)."""
    codigo = request.args.get("codigo", type=str)
    produto_id = request.args.get("produto_id", type=int)

    if not codigo:
        return {"exists": False}

    query = Produto.query.filter(Produto.codigo == codigo)
    if produto_id is not None:
        query = query.filter(Produto.id != int(produto_id))

    produto_existente = query.first()
    return {
        "exists": bool(produto_existente),
        "nome": getattr(produto_existente, "nome", None),
    }


@main_bp.route("/api/buscar_pecas_similares")
@login_required
def buscar_pecas_similares():
    """Busca peças para o campo de autocompletar de similares."""
    termo_busca = request.args.get("q", "").strip()
    produto_atual_id = request.args.get("exclude_id", type=int)

    if not termo_busca or len(termo_busca) < 2:
        return {"items": []}

    query = Produto.query.filter(
        or_(
            Produto.codigo.ilike(f"%{termo_busca}%"),
            Produto.nome.ilike(f"%{termo_busca}%"),
        )
    )
    if produto_atual_id:
        query = query.filter(Produto.id != produto_atual_id)

    resultados = query.limit(10).all()
    items = [{"id": p.id, "codigo": p.codigo, "nome": p.nome} for p in resultados]
    return {"items": items}


@main_bp.route("/api/get_montadora")
@login_required
def get_montadora_for_veiculo():
    """Busca a montadora mais provável para um determinado veículo."""
    veiculo = request.args.get("veiculo", "").strip().upper()
    if not veiculo:
        return {"montadora": None}

    # Usa comparação exata para evitar matches parciais (ex: A1 vs A10)
    aplicacao = (
        Aplicacao.query.filter(func.upper(Aplicacao.veiculo) == veiculo)
        .order_by(Aplicacao.id.desc())
        .first()
    )
    
    # Se não encontrar com comparação exata, tenta busca mais flexível
    if not aplicacao:
        aplicacao = (
            Aplicacao.query.filter(
                db.or_(
                    Aplicacao.veiculo.ilike(f"% {veiculo} %"),
                    Aplicacao.veiculo.ilike(f"{veiculo} %"),
                    Aplicacao.veiculo.ilike(f"% {veiculo}"),
                    Aplicacao.veiculo.ilike(veiculo)
                )
            )
            .order_by(Aplicacao.id.desc())
            .first()
        )
    return {"montadora": aplicacao.montadora if aplicacao else None}


# --- Rota de Atualização da Aplicação ---


@admin_bp.route("/atualizar_aplicacao", methods=["POST"])
def atualizar_aplicacao():
    """
    Baixa o pacote de atualização, o salva e cria o gatilho para
    que o run.py possa instalar a atualização ao reiniciar.
    """
    update_info = current_app.config.get("UPDATE_INFO")
    if not update_info or "download_url" not in update_info:
        flash("Nenhuma informação de atualização encontrada.", "danger")
        return redirect(url_for("main.index"))

    try:
        print(f"Baixando atualização de: {update_info['download_url']}")
        response = requests.get(
            update_info["download_url"], stream=True, timeout=300
        )  # Timeout de 5 minutos
        response.raise_for_status()

        update_package_path = os.path.join(APP_DATA_PATH, "update_package.zip")
        with open(update_package_path, "wb") as f:
            shutil.copyfileobj(response.raw, f)

        # Cria o arquivo "gatilho" para sinalizar que a aplicação deve reiniciar e atualizar
        restart_trigger_file = os.path.join(APP_DATA_PATH, "RESTART_FOR_UPDATE")
        with open(restart_trigger_file, "w") as f:
            f.write("restart_for_update")

        return render_template(
            "reiniciando.html",
            mensagem="Atualização baixada! A aplicação será reiniciada para instalar...",
        )

    except requests.exceptions.RequestException as e:
        flash(f"Erro ao baixar o pacote de atualização: {e}", "danger")
        return redirect(url_for("main.index"))


@admin_bp.route("/peca/<int:produto_id>/sugestao/<int:sugestao_id>/ignorar", methods=["POST", "DELETE"])
def ignorar_sugestao(produto_id, sugestao_id):
    """Marca uma sugestão como ignorada (POST) ou remove a marcação (DELETE).

    POST: cria registro em SugestaoIgnorada para persistir que a sugestão não deve
    mais ser exibida para o produto.

    DELETE: remove o registro, permitindo que a sugestão volte a aparecer.
    Retorna JSON para uso por AJAX e faz redirect/flash quando chamada por POST em formulários.
    """
    produto = db.session.get(Produto, produto_id)
    sugestao = db.session.get(Produto, sugestao_id)

    if not produto or not sugestao:
        if request.method == "DELETE":
            return {"success": False, "message": "Produto ou sugestão não encontrado."}, 404
        flash("Produto ou sugestão não encontrado.", "danger")
        return redirect(request.referrer or url_for("main.index"))

    try:
        existing = (
            db.session.query(SugestaoIgnorada)
            .filter_by(produto_id=produto.id, sugestao_id=sugestao.id)
            .one_or_none()
        )

        if request.method == "POST":
            if not existing:
                novo = SugestaoIgnorada(produto_id=produto.id, sugestao_id=sugestao.id)
                db.session.add(novo)
                db.session.commit()
            if request.is_json or request.method == "POST":
                return {"success": True, "message": "Sugestão ignorada."}
            flash("Sugestão ignorada.", "success")
            return redirect(url_for("main.detalhe_peca", id=produto.id))

        # DELETE
        if existing:
            db.session.delete(existing)
            db.session.commit()
        return {"success": True, "message": "Ignorar removido."}

    except Exception as e:
        db.session.rollback()
        if request.method == "DELETE":
            return {"success": False, "message": f"Erro: {e}"}, 500
        flash(f"Erro ao processar a solicitação: {e}", "danger")
        return redirect(request.referrer or url_for("main.detalhe_peca", id=produto.id))


# --- Rotas de Contatos ---

@main_bp.route("/contatos")
@login_required
def listar_contatos():
    """Lista todos os contatos"""
    page = request.args.get('page', 1, type=int)
    termo = request.args.get('termo', '', type=str)
    favoritos_apenas = request.args.get('favoritos', False, type=bool)
    
    query = Contato.query
    
    if termo:
        termo_norm = _normalize_for_search(termo)
        query = query.filter(
            or_(
                func.lower(Contato.nome).contains(termo_norm),
                func.lower(Contato.empresa).contains(termo_norm),
                func.lower(Contato.telefone).contains(termo_norm),
                func.lower(Contato.email).contains(termo_norm)
            )
        )
    
    if favoritos_apenas:
        query = query.filter(Contato.favorito == True)
    
    contatos = query.order_by(Contato.favorito.desc(), Contato.nome).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('contatos/listar_contatos.html', 
                         contatos=contatos, 
                         termo=termo, 
                         favoritos_apenas=favoritos_apenas)


@main_bp.route("/contatos/adicionar", methods=['GET', 'POST'])
@login_required
def adicionar_contato():
    """Adiciona um novo contato"""
    if request.method == 'POST':
        try:
            contato = Contato(
                nome=request.form['nome'].strip(),
                empresa=request.form.get('empresa', '').strip() or None,
                telefone=request.form.get('telefone', '').strip() or None,
                whatsapp=request.form.get('whatsapp', '').strip() or None,
                email=request.form.get('email', '').strip() or None,
                cargo=request.form.get('cargo', '').strip() or None,
                endereco=request.form.get('endereco', '').strip() or None,
                observacoes=request.form.get('observacoes', '').strip() or None,
                favorito=bool(request.form.get('favorito'))
            )
            
            db.session.add(contato)
            db.session.commit()
            
            flash('Contato adicionado com sucesso!', 'success')
            return redirect(url_for('main.listar_contatos'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao adicionar contato: {str(e)}', 'danger')
    
    return render_template('contatos/adicionar_contato.html')


@main_bp.route("/contatos/<int:id>/editar", methods=['GET', 'POST'])
@login_required
def editar_contato(id):
    """Edita um contato existente"""
    contato = Contato.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            contato.nome = request.form['nome'].strip()
            contato.empresa = request.form.get('empresa', '').strip() or None
            contato.telefone = request.form.get('telefone', '').strip() or None
            contato.whatsapp = request.form.get('whatsapp', '').strip() or None
            contato.email = request.form.get('email', '').strip() or None
            contato.cargo = request.form.get('cargo', '').strip() or None
            contato.endereco = request.form.get('endereco', '').strip() or None
            contato.observacoes = request.form.get('observacoes', '').strip() or None
            contato.favorito = bool(request.form.get('favorito'))
            
            db.session.commit()
            
            flash('Contato atualizado com sucesso!', 'success')
            return redirect(url_for('main.listar_contatos'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar contato: {str(e)}', 'danger')
    
    return render_template('contatos/editar_contato.html', contato=contato)


@main_bp.route("/contatos/<int:id>/deletar", methods=['POST'])
@login_required
def deletar_contato(id):
    """Deleta um contato"""
    if not current_user.is_admin:
        flash('Apenas administradores podem deletar contatos.', 'danger')
        return redirect(url_for('main.listar_contatos'))
    
    contato = Contato.query.get_or_404(id)
    
    try:
        db.session.delete(contato)
        db.session.commit()
        flash(f'Contato "{contato.nome}" deletado com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao deletar contato: {str(e)}', 'danger')
    
    return redirect(url_for('main.listar_contatos'))


@main_bp.route("/contatos/<int:id>/favorito", methods=['POST'])
@login_required
def toggle_favorito_contato(id):
    """Alterna o status de favorito de um contato"""
    contato = Contato.query.get_or_404(id)
    
    try:
        contato.favorito = not contato.favorito
        db.session.commit()
        
        status = "adicionado aos" if contato.favorito else "removido dos"
        flash(f'Contato {status} favoritos!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao atualizar favorito: {str(e)}', 'danger')
    
    return redirect(request.referrer or url_for('main.listar_contatos'))


@main_bp.route("/contatos/<int:id>/whatsapp")
@login_required
def abrir_whatsapp(id):
    """Abre o WhatsApp para o contato"""
    contato = Contato.query.get_or_404(id)
    
    if not contato.whatsapp:
        flash('Este contato não possui WhatsApp cadastrado.', 'warning')
        return redirect(url_for('main.listar_contatos'))
    
    numero_formatado = contato.whatsapp_formatado
    if not numero_formatado:
        flash('Número de WhatsApp inválido.', 'danger')
        return redirect(url_for('main.listar_contatos'))
    
    # Redireciona para o WhatsApp Web
    whatsapp_url = f"https://wa.me/{numero_formatado}"
    
    return redirect(whatsapp_url)


# ==================== ROTAS DO CARRINHO ====================

@main_bp.route("/carrinho")
@login_required
def visualizar_carrinho():
    """Exibe os itens do carrinho"""
    summary = get_cart_summary()
    return render_template('carrinho/visualizar_carrinho.html', 
                         cart_summary=summary)


@main_bp.route("/carrinho/adicionar", methods=["POST"])
@login_required
def adicionar_ao_carrinho():
    """Adiciona um produto ao carrinho"""
    produto_id = request.form.get('produto_id', type=int)
    quantidade = request.form.get('quantidade', 1, type=int)
    observacoes = request.form.get('observacoes', '')
    
    if not produto_id:
        flash('Produto não encontrado.', 'danger')
        return redirect(request.referrer or url_for('main.index'))
    
    produto = Produto.query.get_or_404(produto_id)
    
    if add_to_cart(produto_id, quantidade, observacoes):
        flash(f'"{produto.nome}" foi adicionado ao carrinho!', 'success')
    else:
        flash('Erro ao adicionar produto ao carrinho.', 'danger')
    
    return redirect(request.referrer or url_for('main.visualizar_carrinho'))


@main_bp.route("/carrinho/remover", methods=["POST"])
@login_required
def remover_do_carrinho():
    """Remove um produto do carrinho"""
    produto_id = request.form.get('produto_id', type=int)
    
    if not produto_id:
        flash('Produto não encontrado.', 'danger')
        return redirect(url_for('main.visualizar_carrinho'))
    
    produto = Produto.query.get_or_404(produto_id)
    
    if remove_from_cart(produto_id):
        flash(f'"{produto.nome}" foi removido do carrinho.', 'success')
    else:
        flash('Erro ao remover produto do carrinho.', 'danger')
    
    return redirect(url_for('main.visualizar_carrinho'))


@main_bp.route("/carrinho/atualizar", methods=["POST"])
@login_required
def atualizar_carrinho():
    """Atualiza quantidades e observações dos itens do carrinho"""
    for key, value in request.form.items():
        if key.startswith('quantidade_'):
            produto_id = int(key.split('_')[1])
            quantidade = int(value) if value else 0
            observacoes = request.form.get(f'observacoes_{produto_id}', '')
            
            if quantidade <= 0:
                remove_from_cart(produto_id)
            else:
                update_cart_item(produto_id, quantidade, observacoes)
    
    flash('Carrinho atualizado com sucesso!', 'success')
    return redirect(url_for('main.visualizar_carrinho'))


@main_bp.route("/carrinho/limpar", methods=["POST"])
@login_required
def limpar_carrinho():
    """Limpa todos os itens do carrinho"""
    clear_cart()
    flash('Carrinho foi esvaziado.', 'success')
    return redirect(url_for('main.visualizar_carrinho'))


@main_bp.route("/carrinho/contatos-whatsapp")
@login_required
def carrinho_contatos_whatsapp():
    """Retorna JSON com contatos que possuem WhatsApp cadastrado"""
    contatos = Contato.query.filter(
        Contato.whatsapp.isnot(None),
        Contato.whatsapp != ''
    ).order_by(Contato.favorito.desc(), Contato.nome).all()
    
    resultado = []
    for c in contatos:
        resultado.append({
            'id': c.id,
            'nome': c.nome,
            'empresa': c.empresa or '',
            'whatsapp': c.whatsapp_formatado,
            'favorito': c.favorito
        })
    
    return jsonify(resultado)


@main_bp.route("/carrinho/pdf")
@login_required
def carrinho_pdf():
    """Gera PDF do carrinho"""
    from datetime import datetime
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER
    import tempfile
    import os
    import threading
    import time
    
    # Criar arquivo temporário com nome único
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf', 
                                           prefix='carrinho_')
    temp_path = temp_file.name
    temp_file.close()
    
    try:
        # Obter itens do carrinho
        cart_summary = get_cart_summary()
        
        if not cart_summary['items']:
            flash('O carrinho está vazio. Adicione itens antes de gerar o PDF.', 'warning')
            return redirect(url_for('main.visualizar_carrinho'))
        
        # Configurar documento PDF
        doc = SimpleDocTemplate(temp_path, pagesize=A4,
                               topMargin=2*cm, bottomMargin=2*cm,
                               leftMargin=2*cm, rightMargin=2*cm)
        
        # Estilos
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'],
                                   fontSize=18, textColor=colors.darkblue,
                                   alignment=TA_CENTER, spaceAfter=30)
        
        normal_style = styles['Normal']
        normal_style.fontSize = 10
        
        # Conteúdo do PDF
        story = []
        
        # Título
        story.append(Paragraph("LISTA DE PEÇAS - CARRINHO", title_style))
        story.append(Spacer(1, 20))
        
        # Informações do usuário e data
        info_data = [
            ['Usuário:', current_user.username],
            ['Data:', datetime.now().strftime('%d/%m/%Y %H:%M')],
            ['Total de itens:', str(cart_summary['count'])],
            ['Produtos diferentes:', str(cart_summary['total_produtos'])]
        ]
        
        info_table = Table(info_data, colWidths=[4*cm, 6*cm])
        info_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('GRID', (0, 0), (-1, -1), 1, colors.lightgrey),
        ]))
        
        story.append(info_table)
        story.append(Spacer(1, 30))
        
        # Montar tabela semelhante à lista de resultados: Imagem | Código | Nome | Fornecedor | Ano | Aplicações (todas)
        from flask import current_app
        import re

        # Helper: insere zero-width spaces em sequências longas sem espaços e trunca textos muito longos
        def wrap_and_truncate(text, chunk=20, max_total=800):
            if not text:
                return ''
            # Trunca o texto total se for muito grande
            t = str(text)
            if len(t) > max_total:
                t = t[:max_total-3] + '...'
            # Insere ZWSP em sequências contínuas de caracteres sem espaços para permitir quebra
            # Substitui cada sequência de não-brancos longos por grupos com ZWSP
            pattern = re.compile(r"(\S{%d})" % chunk)
            # Use lambda to insert the zero-width space character to avoid \u escapes in string literals
            return pattern.sub(lambda m: m.group(1) + '\u200b', t)

        table_data = []
        # Estilo específico para a coluna Nome (permite quebra de linha)
        name_style = ParagraphStyle('NameStyle', parent=normal_style, fontSize=10, leading=12, wordWrap='CJK')
        # Estilo reduzido para células de Ano/Aplicações/Motor (evita quebras de linha)
        small_style = ParagraphStyle('SmallCell', parent=normal_style, fontSize=7, leading=8)

        # Cabeçalho
        table_data.append([
            Paragraph('<b>Imagem</b>', normal_style),
            Paragraph('<b>Código</b>', normal_style),
            Paragraph('<b>Nome</b>', normal_style),
            Paragraph('<b>Fornecedor</b>', normal_style),
            Paragraph('<b>Ano</b>', normal_style),
            Paragraph('<b>Aplicações</b>', normal_style),
            Paragraph('<b>Motor</b>', normal_style)
        ])

        for item in cart_summary['items']:
            produto = item['produto']

            # Imagem (usar primeira imagem se existir)
            img_flowable = ''
            try:
                if produto.imagens:
                    fname = produto.imagens[0].filename
                    uploads_folder = current_app.config.get('UPLOAD_FOLDER')
                    if uploads_folder:
                        img_path = os.path.join(uploads_folder, fname)
                        if os.path.exists(img_path):
                            img_flowable = RLImage(img_path, width=2*cm, height=2*cm)
            except Exception:
                img_flowable = ''

            # Código, Nome, Fornecedor
            code_cell = Paragraph(produto.codigo or '', normal_style)
            name_text = wrap_and_truncate(produto.nome or '', chunk=20, max_total=300)
            name_cell = Paragraph(name_text, name_style)
            supplier_cell = Paragraph(produto.fornecedor or '', normal_style)

            # Todas as aplicações — extrair anos separadamente e listar demais campos em Aplicações
            apps_lines = []
            anos_set = []
            motors_set = []
            for aplicacao in produto.aplicacoes:
                parts = []
                if aplicacao.montadora:
                    parts.append(aplicacao.montadora)
                if aplicacao.veiculo:
                    parts.append(aplicacao.veiculo)
                if aplicacao.motor:
                    # Não adicionar o texto do motor em 'parts' (coluna Aplicações);
                    # apenas colecionar o motor para a coluna 'Motor'.
                    try:
                        motor_str = str(aplicacao.motor).strip()
                        if motor_str and motor_str not in motors_set:
                            motors_set.append(motor_str)
                    except Exception:
                        pass
                if aplicacao.ano:
                    # coletar anos para coluna separada
                    try:
                        ano_str = str(aplicacao.ano).strip()
                        if ano_str and ano_str not in anos_set:
                            anos_set.append(ano_str)
                    except Exception:
                        pass
                if parts:
                    apps_lines.append(" ".join(parts))

            # Preparar listas alinhadas por aplicação: ano, aplicação, motor
            if apps_lines:
                # aplicaçoes já contém montadora+veiculo (sem motor)
                app_list = apps_lines
            else:
                app_list = ['Não informadas']

            # Garantir que anos_set e motors_set estejam alinhados com as aplicações na mesma ordem
            # Aqui, coletamos listas na mesma ordem das aplicações originais
            anos_list = []
            motors_list = []
            for aplicacao in produto.aplicacoes:
                try:
                    anos_list.append(str(aplicacao.ano).strip() if aplicacao.ano else '')
                except Exception:
                    anos_list.append('')
                try:
                    motors_list.append(str(aplicacao.motor).strip() if aplicacao.motor else '')
                except Exception:
                    motors_list.append('')

            # Se não houver aplicações, criar uma linha vazia para ano/motor
            if not anos_list:
                anos_list = ['']
            if not motors_list:
                motors_list = ['']

            # Trunca e insere ZWSP nos textos de aplicações
            app_list = [wrap_and_truncate(a, chunk=25, max_total=800) for a in app_list]

            # Agora criar uma linha por aplicação, alinhando ano/aplicação/motor
            max_rows = max(len(app_list), len(anos_list), len(motors_list))
            for i in range(max_rows):
                year_cell = anos_list[i] if i < len(anos_list) else ''
                motor_cell = motors_list[i] if i < len(motors_list) else ''
                app_cell = app_list[i] if i < len(app_list) else ''

                year_par = Paragraph(year_cell.replace('\n', '<br/>'), small_style) if year_cell else Paragraph('', small_style)
                app_par = Paragraph(app_cell.replace('\n', '<br/>'), small_style) if app_cell else Paragraph('', small_style)
                motor_par = Paragraph(motor_cell, small_style) if motor_cell else Paragraph('', small_style)

                if i == 0:
                    table_data.append([img_flowable, code_cell, name_cell, supplier_cell, year_par, app_par, motor_par])
                else:
                    # linhas seguintes sem imagem/código/nome/fornecedor repetidos
                    table_data.append(['', '', '', '', year_par, app_par, motor_par])

        # Ajuste de larguras para caber dentro da área imprimível (A4 - margens 2cm)
        # Soma aproximada deve ficar <= 17cm (21cm largura total - 4cm margens)
        col_widths = [1.8*cm, 2.5*cm, 5.0*cm, 2.0*cm, 1.6*cm, 2.2*cm, 1.4*cm]
        products_table = Table(table_data, colWidths=col_widths, hAlign='LEFT')
        products_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('GRID', (0, 0), (-1, -1), 0.4, colors.lightgrey),
            ('BACKGROUND', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('LEFTPADDING', (0,0), (-1,-1), 4),
            ('RIGHTPADDING', (0,0), (-1,-1), 4),
            ('ALIGN', (0,0), (0,-1), 'CENTER'),
            ('ALIGN', (1,0), (1,-1), 'LEFT'),
            ('ALIGN', (2,0), (2,-1), 'LEFT'),
            ('ALIGN', (3,0), (3,-1), 'LEFT'),
            ('ALIGN', (4,0), (4,-1), 'LEFT'),
            ('ALIGN', (5,0), (5,-1), 'LEFT'),
            ('ALIGN', (6,0), (6,-1), 'LEFT'),
        ]))

        story.append(products_table)
        
        story.append(Spacer(1, 20))
        
        # Rodapé
        footer = Paragraph(f"Documento gerado automaticamente pelo Sistema de Catálogo de Peças", 
                         ParagraphStyle('Footer', parent=normal_style, 
                                      fontSize=8, textColor=colors.grey, 
                                      alignment=TA_CENTER))
        story.append(footer)
        
        # Gerar PDF
        doc.build(story)
        
        # Função para deletar arquivo após delay (em thread separada)
        def delayed_cleanup(file_path, delay=30):
            """Tenta deletar o arquivo após um delay"""
            time.sleep(delay)
            try:
                if os.path.exists(file_path):
                    os.unlink(file_path)
            except (PermissionError, OSError):
                pass  # Arquivo ainda pode estar em uso
        
        # Iniciar cleanup em background
        cleanup_thread = threading.Thread(target=delayed_cleanup, args=(temp_path,))
        cleanup_thread.daemon = True
        cleanup_thread.start()
        
        # Enviar arquivo
        return send_file(temp_path, 
                        as_attachment=True,
                        download_name=f'carrinho_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf',
                        mimetype='application/pdf')
    
    except Exception as e:
        # Em caso de erro, tentar deletar o arquivo imediatamente
        try:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
        except (PermissionError, OSError):
            pass
        
        flash(f'Erro ao gerar PDF: {str(e)}', 'danger')
        return redirect(url_for('main.visualizar_carrinho'))


# ==================== ROTAS DO DASHBOARD ANALYTICS ====================

@admin_bp.route("/dashboard")
@login_required
def dashboard():
    """Dashboard de analytics e estatísticas do sistema"""
    try:
        # Coleta estatísticas
        stats_data = collect_dashboard_stats()
        chart_data = prepare_chart_data()
        
        return render_template('dashboard.html', 
                             stats=stats_data, 
                             chart_data=chart_data)
                             
    except Exception as e:
        flash(f'Erro ao carregar dashboard: {str(e)}', 'danger')
        return redirect(url_for('main.index'))


@admin_bp.route("/dashboard/refresh")
@login_required
def dashboard_refresh():
    """Endpoint AJAX para atualizar dados do dashboard"""
    try:
        stats_data = collect_dashboard_stats()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'success': True,
                'stats': stats_data,
                'timestamp': datetime.now().isoformat()
            })
        else:
            return redirect(url_for('admin.dashboard'))
            
    except Exception as e:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
        else:
            flash(f'Erro ao atualizar dados: {str(e)}', 'danger')
            return redirect(url_for('admin.dashboard'))


def collect_dashboard_stats():
    """Coleta todas as estatísticas para o dashboard"""
    from datetime import datetime, timedelta
    
    stats = {
        'timestamp': datetime.now(),
        'produtos': {},
        'aplicacoes': {},
        'fornecedores': {},
        'imagens': {},
        'cache': {},
        'fts': {},
        'db_size_mb': 0,
        'produtos_populares': [],
        'montadoras_ranking': []
    }
    
    # Estatísticas de produtos
    total_produtos = Produto.query.count()
    stats['produtos'] = {
        'total': total_produtos,
        'crescimento_texto': 'Catálogo completo'
    }
    
    # Estatísticas de aplicações
    total_aplicacoes = Aplicacao.query.count()
    stats['aplicacoes'] = {
        'total': total_aplicacoes,
        'crescimento_texto': 'Aplicações compatíveis'
    }
    
    # Estatísticas de fornecedores
    total_fornecedores = db.session.query(Produto.fornecedor).distinct().count()
    stats['fornecedores'] = {
        'total': total_fornecedores,
        'crescimento_texto': 'Fornecedores cadastrados'
    }
    
    # Estatísticas de imagens
    total_imagens = ImagemProduto.query.count()
    stats['imagens'] = {
        'total': total_imagens,
        'crescimento_texto': 'Imagens no catálogo'
    }
    
    # Estatísticas de cache (se disponível)
    try:
        from utils.cache_system import get_cache_stats
        cache_stats = get_cache_stats()
        stats['cache'] = {
            'hit_rate': cache_stats['app_cache']['hit_rate'],
            'total_keys': cache_stats['app_cache']['size']
        }
    except (ImportError, Exception):
        stats['cache'] = {
            'hit_rate': 0,
            'total_keys': 0
        }
    
    # Estatísticas FTS5 (se disponível) 
    try:
        from utils.fts_search import get_fts_manager
        fts_manager = get_fts_manager()
        fts_stats = fts_manager.get_stats()
        stats['fts'] = {
            'ativo': fts_stats['exists'],
            'total_records': fts_stats['total_records']
        }
    except (ImportError, Exception):
        stats['fts'] = {
            'ativo': False,
            'total_records': 0
        }
    
    # Tamanho do banco de dados
    try:
        import os
        from app import APP_DATA_PATH
        db_path = os.path.join(APP_DATA_PATH, 'catalogo.db')
        if os.path.exists(db_path):
            size_bytes = os.path.getsize(db_path)
            stats['db_size_mb'] = round(size_bytes / (1024 * 1024), 1)
    except Exception:
        stats['db_size_mb'] = 0
    
    # Produtos mais populares (por número de aplicações)
    produtos_populares_raw = db.session.query(
        Produto,
        func.count(func.distinct(Aplicacao.id)).label('total_aplicacoes'),
        func.count(func.distinct(ImagemProduto.id)).label('total_imagens'),
        func.count(func.distinct(similares_association.c.similar_id)).label('total_similares')
    ).outerjoin(Aplicacao).outerjoin(ImagemProduto).outerjoin(
        similares_association, Produto.id == similares_association.c.produto_id
    ).group_by(Produto.id).order_by(
        func.count(func.distinct(Aplicacao.id)).desc()
    ).limit(10).all()
    
    produtos_populares = []
    for row in produtos_populares_raw:
        p = row[0]
        p.total_aplicacoes = row[1]
        p.total_imagens = row[2]
        p.total_similares = row[3]
        produtos_populares.append(p)
    
    stats['produtos_populares'] = produtos_populares
    
    # Ranking de montadoras
    montadoras_stats = db.session.query(
        Aplicacao.montadora,
        func.count(Aplicacao.id).label('total_aplicacoes'),
        func.count(func.distinct(Aplicacao.produto_id)).label('produtos_unicos')
    ).filter(
        Aplicacao.montadora.isnot(None),
        Aplicacao.montadora != ''
    ).group_by(Aplicacao.montadora).order_by(
        func.count(Aplicacao.id).desc()
    ).limit(10).all()
    
    # Calcula percentuais
    total_apps = sum(m[1] for m in montadoras_stats)
    montadoras_ranking = []
    for nome, total_apps_montadora, produtos_unicos in montadoras_stats:
        percentual = (total_apps_montadora / total_apps * 100) if total_apps > 0 else 0
        montadoras_ranking.append({
            'montadora': nome,
            'total_aplicacoes': total_apps_montadora,
            'produtos_unicos': produtos_unicos,
            'percentual': percentual
        })
    
    stats['montadoras_ranking'] = montadoras_ranking
    
    return stats


def prepare_chart_data():
    """Prepara dados para os gráficos no dashboard"""
    chart_data = {
        'fornecedores': {'labels': [], 'data': []},
        'montadoras': {'labels': [], 'data': []},
        'grupos': {'labels': [], 'data': []},
        'imagens': {'labels': [], 'data': []}
    }
    
    # Top 10 fornecedores por número de produtos
    fornecedores_data = db.session.query(
        Produto.fornecedor,
        func.count(Produto.id).label('total')
    ).filter(
        Produto.fornecedor.isnot(None),
        Produto.fornecedor != ''
    ).group_by(Produto.fornecedor).order_by(
        func.count(Produto.id).desc()
    ).limit(10).all()
    
    chart_data['fornecedores']['labels'] = [f[0] for f in fornecedores_data]
    chart_data['fornecedores']['data'] = [f[1] for f in fornecedores_data]
    
    # Top 10 montadoras por número de aplicações
    montadoras_data = db.session.query(
        Aplicacao.montadora,
        func.count(Aplicacao.id).label('total')
    ).filter(
        Aplicacao.montadora.isnot(None),
        Aplicacao.montadora != ''
    ).group_by(Aplicacao.montadora).order_by(
        func.count(Aplicacao.id).desc()
    ).limit(10).all()
    
    chart_data['montadoras']['labels'] = [m[0] for m in montadoras_data]
    chart_data['montadoras']['data'] = [m[1] for m in montadoras_data]
    
    # Grupos de produtos
    grupos_data = db.session.query(
        Produto.grupo,
        func.count(Produto.id).label('total')
    ).filter(
        Produto.grupo.isnot(None),
        Produto.grupo != ''
    ).group_by(Produto.grupo).order_by(
        func.count(Produto.id).desc()
    ).limit(10).all()
    
    chart_data['grupos']['labels'] = [g[0] for g in grupos_data]
    chart_data['grupos']['data'] = [g[1] for g in grupos_data]
    
    # Simplificado: produtos com/sem imagens
    produtos_com_img = db.session.query(func.count(func.distinct(ImagemProduto.produto_id))).scalar() or 0
    produtos_sem_img = Produto.query.count() - produtos_com_img
    
    chart_data['imagens']['labels'] = ['Com Imagens', 'Sem Imagens']
    chart_data['imagens']['data'] = [produtos_com_img, produtos_sem_img]
    
    return chart_data
