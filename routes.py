import os
import json
import collections
import threading
import zipfile
from datetime import datetime
from flask import (Blueprint, render_template, request, redirect, url_for, flash, jsonify,
                   Response, send_from_directory, current_app)
from flask_login import login_user, logout_user, login_required, current_user
from sqlalchemy import func, or_
from sqlalchemy.orm import selectinload
from werkzeug.utils import secure_filename

from app import db, carregar_config_aparencia, salvar_config_aparencia, APP_DATA_PATH
from models import Produto, Aplicacao, ImagemProduto, User
from core_utils import (_build_search_query, _atualizar_similares_simetricamente, 
                        _parse_year_range, _ranges_overlap, _get_form_datalists, allowed_file)
from image_utils import download_image_from_url

# --- Gerenciamento de Tarefas em Segundo Plano ---
import subprocess
import sys
TASK_STATUS = {"status": "Ocioso", "output": ""}

# --- Criação dos Blueprints ---
main_bp = Blueprint('main', __name__)
auth_bp = Blueprint('auth', __name__)
admin_bp = Blueprint('admin', __name__, url_prefix='/admin') # Rotas de admin terão prefixo /admin

# --- Rotas Principais (main_bp) ---

@main_bp.route('/')
def index():
    """Página inicial que exibe a busca e a lista de montadoras com seus veículos."""
    aplicacoes = db.session.query(Aplicacao.montadora, Aplicacao.veiculo).distinct().filter(
        Aplicacao.montadora.isnot(None), 
        Aplicacao.montadora != ''
    ).order_by(Aplicacao.montadora, Aplicacao.veiculo).all()

    montadoras_com_veiculos = collections.defaultdict(list)
    for montadora, veiculo in aplicacoes:
        montadoras_com_veiculos[montadora.strip().title()].append(veiculo)

    return render_template('index.html', montadoras_com_veiculos=dict(sorted(montadoras_com_veiculos.items())), show_top_search=False)

@main_bp.route('/buscar')
def buscar():
    """Página de resultados da busca."""
    page = request.args.get('page', 1, type=int)
    termo = request.args.get('termo', '')
    codigo_produto = request.args.get('codigo_produto', '')
    montadora = request.args.get('montadora', '')
    aplicacao_termo = request.args.get('aplicacao', '')
    grupo = request.args.get('grupo', '')
    medidas = request.args.get('medidas', '')
    sort_by = request.args.get('sort_by', 'codigo')
    sort_dir = request.args.get('sort_dir', 'asc')

    PER_PAGE = 20
    query = _build_search_query(termo, codigo_produto, montadora, aplicacao_termo, grupo, medidas)

    # Define a coluna de ordenação
    order_column = Produto.codigo
    if sort_by == 'nome':
        order_column = Produto.nome
    
    # Aplica a direção da ordenação
    if sort_dir == 'desc':
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
        pagination = query.distinct().paginate(page=page, per_page=PER_PAGE, error_out=False)
        produtos_paginados = pagination.items

        for produto in produtos_paginados:
            # Filtra as aplicações do produto para mostrar apenas as que batem com a busca
            aplicacoes_relevantes = [
                app for app in produto.aplicacoes 
                if (not montadora or montadora.lower() in app.montadora.lower()) and \
                   (not aplicacao_termo or aplicacao_termo.lower() in (app.veiculo or '').lower())
            ]
            for aplicacao in aplicacoes_relevantes:
                chave_agrupamento = f"{aplicacao.montadora} {aplicacao.veiculo} {aplicacao.ano or ''}".strip()
                if produto not in resultados_agrupados[chave_agrupamento]:
                    resultados_agrupados[chave_agrupamento].append(produto)
        resultados_agrupados = dict(sorted(resultados_agrupados.items()))
    else:
        # Busca padrão sem agrupamento
        pagination = query.distinct().paginate(page=page, per_page=PER_PAGE, error_out=False)

    return render_template(
        'resultados.html', 
        pagination=pagination, 
        termo=termo, 
        sort_by=sort_by,
        sort_dir=sort_dir,
        resultados_agrupados=resultados_agrupados,
        endpoint=request.endpoint  # Passa o endpoint atual para o template
    )

@main_bp.route('/peca/<int:id>')
def detalhe_peca(id):
    """Exibe a página de detalhes de um produto específico."""
    produto = db.session.query(Produto).options(
        selectinload(Produto.aplicacoes),
        selectinload(Produto.imagens),
        selectinload(Produto.similares).selectinload(Produto.aplicacoes), # Carrega aplicações dos similares
        selectinload(Produto.similares).selectinload(Produto.imagens),    # Carrega imagens dos similares
        selectinload(Produto.similar_to)
    ).get(id)
    if not produto:
        flash('Produto não encontrado.', 'danger')
        return redirect(url_for('main.index'))

    aplicacoes_agrupadas = collections.defaultdict(list)
    sorted_aplicacoes = sorted(produto.aplicacoes, key=lambda app: (app.montadora or 'ZZZ', app.veiculo or ''))
    for aplicacao in sorted_aplicacoes:
        montadora_chave = aplicacao.montadora or 'Sem Montadora'
        aplicacoes_agrupadas[montadora_chave].append(aplicacao)

    # Lógica para encontrar produtos sugeridos
    sugestoes_similares_dict = {}
    ids_ja_relacionados = {p.id for p in produto.similares} | {p.id for p in produto.similar_to} | {produto.id}

    codigos_conversao = [c.strip() for c in (produto.conversoes or '').split(',') if c.strip()]
    if codigos_conversao:
        sugestoes_por_conversao = Produto.query.filter(
            Produto.id.notin_(ids_ja_relacionados),
            Produto.codigo.in_(codigos_conversao)
        ).options(selectinload(Produto.aplicacoes), selectinload(Produto.imagens)).all()
        for p in sugestoes_por_conversao: sugestoes_similares_dict[p.id] = p

    sugestoes_por_codigo_produto = Produto.query.filter(
        Produto.id.notin_(ids_ja_relacionados),
        Produto.conversoes.ilike(f'%{produto.codigo}%')
    ).options(selectinload(Produto.aplicacoes), selectinload(Produto.imagens)).all()
    for p in sugestoes_por_codigo_produto: sugestoes_similares_dict[p.id] = p

    if produto.grupo and produto.aplicacoes:
        for app_principal in produto.aplicacoes:
            if not app_principal.veiculo: continue
            range_principal = _parse_year_range(app_principal.ano)
            if range_principal == (-1, -1): continue

            candidatos = Produto.query.filter(
                Produto.id.notin_(ids_ja_relacionados | set(sugestoes_similares_dict.keys())),
                Produto.grupo == produto.grupo,
                Produto.aplicacoes.any(Aplicacao.veiculo == app_principal.veiculo)
            ).options(selectinload(Produto.aplicacoes), selectinload(Produto.imagens)).all()

            for candidato in candidatos:
                for app_candidata in candidato.aplicacoes:
                    if app_candidata.veiculo == app_principal.veiculo:
                        range_candidato = _parse_year_range(app_candidata.ano)
                        if range_candidato != (-1, -1) and _ranges_overlap(range_principal, range_candidato):
                            sugestoes_similares_dict[candidato.id] = candidato
                            break

    sugestoes_similares = list(sugestoes_similares_dict.values())

    voltar_url = request.referrer or url_for('main.index')
    ignore_referrer = ['/login', '/adicionar_peca', '/editar', '/configuracoes', '/gerenciar_usuarios']
    if any(x in voltar_url for x in ignore_referrer):
        # Se veio de uma página administrativa, voltar para a busca com os argumentos preservados
        # é mais útil do que voltar para o index.
        search_args = request.args.copy()
        search_args.pop('page', None) # Remove a página para voltar à primeira página da busca
        voltar_url = url_for('main.buscar', **search_args)

    return render_template('detalhe_peca.html', produto=produto, aplicacoes_agrupadas=aplicacoes_agrupadas, sugestoes_similares=sugestoes_similares, voltar_url=voltar_url)


# --- Rotas de Autenticação (auth_bp) ---

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated: # type: ignore
        return redirect(url_for('main.index'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user is None or not user.check_password(password):
            flash('Usuário ou senha inválidos.', 'danger')
            return redirect(url_for('auth.login'))
        login_user(user, remember=True)
        return redirect(url_for('main.index'))
    return render_template('login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))


# --- Rotas de Administração (admin_bp) ---

@admin_bp.before_request
@login_required
def require_admin():
    """Garante que todas as rotas neste blueprint sejam acessadas apenas por admins."""
    if not current_user.is_admin: # type: ignore
        flash('Acesso não autorizado. Apenas administradores podem acessar esta área.', 'danger')
        return redirect(url_for('main.index'))

@admin_bp.route('/peca/adicionar', methods=['GET', 'POST'])
def adicionar_peca():
    if request.method == 'POST':
        nome = request.form.get('nome', '').strip().upper()
        codigo = request.form.get('codigo', '').strip().upper()
        if not nome or not codigo:
            flash('Nome da Peça e Código são campos obrigatórios.', 'danger')
            return redirect(url_for('admin.adicionar_peca'))

        if Produto.query.filter(func.upper(Produto.codigo) == codigo).first():
            flash(f'O código "{codigo}" já está em uso. Por favor, escolha outro.', 'danger')
            return redirect(url_for('admin.adicionar_peca'))

        try:
            novo_produto = Produto(
                nome=nome,
                codigo=codigo,
                grupo=request.form.get('grupo', '').strip().upper(),
                fornecedor=request.form.get('fornecedor', '').strip().upper(),
                conversoes=request.form.get('conversoes', '').strip().upper(),
                medidas=request.form.get('medidas', '').strip().upper(),
                observacoes=request.form.get('observacoes', '').strip().upper()
            )
            db.session.add(novo_produto)
            db.session.flush()

            # Lógica de upload e download de imagens
            # A rota 'uploaded_file' está no app principal, não em um blueprint.
            # O caminho para salvar o arquivo deve ser o caminho do sistema, não uma URL.
            proxima_ordem = 0
            files = request.files.getlist('imagens')
            for file in files:
                if file and file.filename != '' and allowed_file(file.filename):
                    _, ext = os.path.splitext(file.filename)
                    timestamp = datetime.now().strftime('%Y%m%d%H%M%S%f')
                    imagem_filename = secure_filename(f"{novo_produto.codigo}_{timestamp}{ext}")
                    file.save(os.path.join(APP_DATA_PATH, 'uploads', imagem_filename))
                    nova_imagem = ImagemProduto(filename=imagem_filename, ordem=proxima_ordem)
                    novo_produto.imagens.append(nova_imagem)
                    proxima_ordem += 1

            imagem_url = request.form.get('imagem_url')
            if imagem_url:
                downloaded_filename = download_image_from_url(imagem_url, os.path.join(APP_DATA_PATH, 'uploads'), product_code=novo_produto.codigo)
                if downloaded_filename:
                    nova_imagem = ImagemProduto(filename=downloaded_filename, ordem=proxima_ordem)
                    novo_produto.imagens.append(nova_imagem)

            # Lógica de similares
            similares_ids = [int(id) for id in request.form.get('similares_ids', '').split(',') if id.isdigit()]
            produtos_similares = Produto.query.filter(Produto.id.in_(similares_ids)).all() if similares_ids else []
            _atualizar_similares_simetricamente(novo_produto, produtos_similares)
            
            # Processa aplicações
            aplicacoes_form = {}
            for key, value in request.form.items():
                if key.startswith('aplicacoes-'):
                    parts = key.split('-')
                    index, field = parts[1], parts[2]
                    aplicacoes_form.setdefault(index, {})[field] = value.strip().upper()

            for data in aplicacoes_form.values():
                if data.get('veiculo'):
                    # Nunca envie 'id' ao criar uma nova Aplicacao
                    filtered = {k: v for k, v in data.items() if k != 'id'}
                    db.session.add(Aplicacao(produto=novo_produto, **filtered))

            db.session.commit()
            flash('Produto adicionado com sucesso!', 'success')
            return redirect(url_for('main.detalhe_peca', id=novo_produto.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Ocorreu um erro inesperado ao adicionar o produto: {e}', 'danger')

    datalists = _get_form_datalists(app_context=current_app)
    return render_template('adicionar_peca.html', **datalists)

@admin_bp.route('/peca/<int:id>/editar', methods=['GET', 'POST'])
def editar_peca(id):
    produto = db.session.query(Produto).options(selectinload(Produto.aplicacoes), selectinload(Produto.imagens), selectinload(Produto.similares)).get(id)
    if not produto:
        flash('Produto não encontrado.', 'danger')
        return redirect(url_for('main.index'))

    voltar_url = request.referrer or url_for('main.detalhe_peca', id=id)

    if request.method == 'POST':
        nome = request.form.get('nome', '').strip().upper()
        codigo = request.form.get('codigo', '').strip().upper()
        if not nome or not codigo:
            flash('Nome da Peça e Código são campos obrigatórios.', 'danger')
            return redirect(url_for('admin.editar_peca', id=id))

        produto_existente = Produto.query.filter(func.upper(Produto.codigo) == codigo, Produto.id != id).first()
        if produto_existente:
            flash(f'O código "{codigo}" já está em uso pelo produto "{produto_existente.nome}".', 'danger')
            return redirect(url_for('admin.editar_peca', id=id))

        try:
            produto.nome = nome
            produto.codigo = codigo
            produto.grupo = request.form.get('grupo', '').strip().upper()
            produto.fornecedor = request.form.get('fornecedor', '').strip().upper()
            produto.conversoes = request.form.get('conversoes', '').strip().upper()
            produto.medidas = request.form.get('medidas', '').strip().upper()
            produto.observacoes = request.form.get('observacoes', '').strip().upper()

            similares_ids = [int(id) for id in request.form.get('similares_ids', '').split(',') if id.isdigit()]
            produtos_similares = Produto.query.filter(Produto.id.in_(similares_ids)).all() if similares_ids else []
            _atualizar_similares_simetricamente(produto, produtos_similares)

            aplicacoes_form = {}
            for key, value in request.form.items():
                if key.startswith('aplicacoes-'):
                    parts = key.split('-')
                    index, field = parts[1], parts[2]
                    aplicacoes_form.setdefault(index, {})[field] = value.strip().upper()

            aplicacoes_existentes_map = {str(app.id): app for app in produto.aplicacoes if app.id}
            ids_aplicacoes_no_form = {data.get('id') for data in aplicacoes_form.values() if data.get('id')}

            for data in aplicacoes_form.values():
                if not data.get('veiculo'): continue
                app_id = data.get('id')
                if app_id and app_id in aplicacoes_existentes_map:
                    aplicacao = aplicacoes_existentes_map[app_id]
                    for field, value in data.items():
                        if field != 'id': setattr(aplicacao, field, value)
                elif data.get('veiculo'):
                    # Nunca envie 'id' ao criar uma nova Aplicacao
                    filtered_new = {k: v for k, v in data.items() if k != 'id'}
                    db.session.add(Aplicacao(produto=produto, **filtered_new))
            
            ids_para_remover = set(aplicacoes_existentes_map.keys()) - ids_aplicacoes_no_form
            for app_id in ids_para_remover:
                db.session.delete(aplicacoes_existentes_map[app_id])

            proxima_ordem = max([img.ordem for img in produto.imagens] + [-1]) + 1
            files = request.files.getlist('imagens')
            for file in files:
                if file and file.filename != '' and allowed_file(file.filename):
                    _, ext = os.path.splitext(file.filename)
                    timestamp = datetime.now().strftime('%Y%m%d%H%M%S%f')
                    imagem_filename = secure_filename(f"{produto.codigo}_{timestamp}{ext}")
                    file.save(os.path.join(APP_DATA_PATH, 'uploads', imagem_filename))
                    nova_imagem = ImagemProduto(filename=imagem_filename, ordem=proxima_ordem)
                    produto.imagens.append(nova_imagem)
                    proxima_ordem += 1

            imagem_url = request.form.get('imagem_url')
            if imagem_url:
                downloaded_filename = download_image_from_url(imagem_url, os.path.join(APP_DATA_PATH, 'uploads'), product_code=produto.codigo)
                if downloaded_filename:
                    nova_imagem = ImagemProduto(filename=downloaded_filename, ordem=proxima_ordem)
                    produto.imagens.append(nova_imagem)

            ordem_imagens_str = request.form.get('ordem_imagens')
            if ordem_imagens_str:
                ordem_ids = ordem_imagens_str.split(',')
                imagens_existentes_map = {str(img.id): img for img in produto.imagens if img.id is not None}
                for i, img_id in enumerate(ordem_ids):
                    if img_id in imagens_existentes_map:
                        imagens_existentes_map[img_id].ordem = i
                
                novas_imagens = [img for img in produto.imagens if img.id is None]
                for i, nova_img in enumerate(novas_imagens, start=len(ordem_ids)):
                    nova_img.ordem = i

            db.session.commit()
            flash('Produto atualizado com sucesso!', 'success')
            return redirect(url_for('main.detalhe_peca', id=produto.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Ocorreu um erro inesperado ao atualizar o produto: {e}', 'danger')

    datalists = _get_form_datalists(app_context=current_app)
    return render_template('editar_peca.html', produto=produto, voltar_url=voltar_url, **datalists)

@admin_bp.route('/peca/<int:id>/clonar', methods=['GET'])
def clonar_peca(id):
    produto_original = db.session.query(Produto).options(
        db.joinedload(Produto.imagens),
        db.joinedload(Produto.aplicacoes),
        db.joinedload(Produto.similares)
    ).filter_by(id=id).one_or_none()

    if not produto_original:
        flash('Produto original não encontrado.', 'danger')
        return redirect(url_for('main.index'))

    clone_suffix = f"CLONE-{datetime.now().strftime('%H%M%S')}"
    novo_produto = Produto(
        nome=produto_original.nome,
        codigo=f"{produto_original.codigo}-{clone_suffix}",
        grupo=produto_original.grupo,
        fornecedor=produto_original.fornecedor,
        conversoes=produto_original.conversoes,
        medidas=produto_original.medidas,
        observacoes=produto_original.observacoes
    )

    for imagem_original in produto_original.imagens:
        novo_produto.imagens.append(ImagemProduto(filename=imagem_original.filename, ordem=imagem_original.ordem))

    novo_produto.similares = list(produto_original.similares)

    for aplicacao_original in produto_original.aplicacoes:
        db.session.add(Aplicacao(produto=novo_produto, **{c.name: getattr(aplicacao_original, c.name) for c in aplicacao_original.__table__.columns if c.name not in ['id', 'produto_id']}))

    db.session.add(novo_produto)
    db.session.commit()

    flash('Produto clonado com sucesso! Por favor, revise o código e os outros dados.', 'success')
    return redirect(url_for('admin.editar_peca', id=novo_produto.id))

@admin_bp.route('/peca/<int:id>/excluir', methods=['POST'])
def excluir_peca(id):
    produto = db.session.query(Produto).options(db.joinedload(Produto.imagens)).filter_by(id=id).one_or_none()
    if not produto:
        flash('Produto não encontrado.', 'danger')
        return redirect(url_for('main.index'))

    if produto.imagens:
        filenames_to_check = {img.filename for img in produto.imagens}
        filenames_in_use_elsewhere = {res[0] for res in db.session.query(ImagemProduto.filename).filter(ImagemProduto.filename.in_(filenames_to_check), ImagemProduto.produto_id != produto.id).distinct()}
        files_to_delete = filenames_to_check - filenames_in_use_elsewhere
        for filename in files_to_delete:
            try:
                os.remove(os.path.join(APP_DATA_PATH, 'uploads', filename))
            except OSError as e:
                print(f"Erro ao tentar remover o arquivo de imagem {filename}: {e}")

    db.session.delete(produto)
    db.session.commit()
    
    flash('Produto excluído com sucesso.', 'success')
    return redirect(url_for('main.index'))

@admin_bp.route('/imagem/<int:id>/excluir', methods=['POST', 'DELETE'])
def excluir_imagem(id):
    imagem = db.session.get(ImagemProduto, id)
    if not imagem:
        return ({"success": False, "message": "Imagem não encontrada"}, 404) if request.method == 'DELETE' else redirect(request.referrer or url_for('main.index'))

    produto_id = imagem.produto_id
    filename = imagem.filename
    db.session.delete(imagem)
    db.session.commit()

    if ImagemProduto.query.filter_by(filename=filename).count() == 0:
        filepath = os.path.join(APP_DATA_PATH, 'uploads', filename)
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except OSError as e:
                print(f"Erro ao tentar remover o arquivo de imagem {filename}: {e}")

    if request.method == 'DELETE':
        return {"success": True, "message": "Imagem excluída com sucesso."}
    else:
        flash('Imagem excluída com sucesso.', 'success')
        return redirect(url_for('admin.editar_peca', id=produto_id))

@admin_bp.route('/aplicacao/<int:id>/excluir_ajax', methods=['DELETE'])
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


@admin_bp.route('/aplicacao/adicionar', methods=['GET', 'POST'])
def adicionar_aplicacao():
    # Espera produto_id em query string ou form
    produto_id = request.values.get('produto_id', type=int)
    produto = db.session.get(Produto, produto_id) if produto_id else None
    if request.method == 'POST':
        veiculo = request.form.get('veiculo', '').strip().upper()
        ano = request.form.get('ano', '').strip().upper()
        motor = request.form.get('motor', '').strip().upper()
        conf_mtr = request.form.get('conf_mtr', '').strip().upper()
        montadora = request.form.get('montadora', '').strip().upper()
        if not produto:
            flash('Produto não encontrado para adicionar aplicação.', 'danger')
            return redirect(url_for('main.index'))
        if not veiculo:
            flash('Veículo é obrigatório.', 'danger')
            return redirect(url_for('admin.gerenciar_aplicacoes', produto_id=produto.id))
        nova = Aplicacao(produto=produto, veiculo=veiculo, ano=ano, motor=motor, conf_mtr=conf_mtr, montadora=montadora)
        db.session.add(nova)
        db.session.commit()
        flash('Aplicação adicionada com sucesso.', 'success')
        return redirect(url_for('main.detalhe_peca', id=produto.id))

    # GET: renderiza o formulário mínimo
    return render_template('adicionar_aplicacao.html', produto=produto)


@admin_bp.route('/aplicacao/<int:id>/editar', methods=['GET', 'POST'])
def editar_aplicacao(id):
    aplicacao = db.session.get(Aplicacao, id)
    if not aplicacao:
        flash('Aplicação não encontrada.', 'danger')
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        aplicacao.veiculo = request.form.get('veiculo', '').strip().upper()
        aplicacao.ano = request.form.get('ano', '').strip().upper()
        aplicacao.motor = request.form.get('motor', '').strip().upper()
        aplicacao.conf_mtr = request.form.get('conf_mtr', '').strip().upper()
        db.session.commit()
        flash('Aplicação atualizada com sucesso.', 'success')
        return redirect(url_for('main.detalhe_peca', id=aplicacao.produto_id))

    return render_template('editar_aplicacao.html', aplicacao=aplicacao)


@admin_bp.route('/aplicacoes/<int:produto_id>', methods=['GET', 'POST'])
def gerenciar_aplicacoes(produto_id):
    produto = db.session.get(Produto, produto_id)
    if not produto:
        flash('Produto não encontrado.', 'danger')
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        veiculo = request.form.get('veiculo', '').strip().upper()
        ano = request.form.get('ano', '').strip().upper()
        motor = request.form.get('motor', '').strip().upper()
        conf_mtr = request.form.get('conf_mtr', '').strip().upper()
        if not veiculo:
            flash('Veículo é obrigatório para a aplicação.', 'danger')
            return redirect(url_for('admin.gerenciar_aplicacoes', produto_id=produto.id))
        nova = Aplicacao(produto=produto, veiculo=veiculo, ano=ano, motor=motor, conf_mtr=conf_mtr)
        db.session.add(nova)
        db.session.commit()
        flash('Aplicação adicionada com sucesso.', 'success')
        return redirect(url_for('admin.gerenciar_aplicacoes', produto_id=produto.id))

    return render_template('gerenciar_aplicacoes.html', produto=produto)


@admin_bp.route('/aplicacao/<int:id>/excluir', methods=['POST'])
def excluir_aplicacao(id):
    aplicacao = db.session.get(Aplicacao, id)
    if not aplicacao:
        flash('Aplicação não encontrada.', 'danger')
        return redirect(url_for('main.index'))
    produto_id = aplicacao.produto_id
    try:
        db.session.delete(aplicacao)
        db.session.commit()
        flash('Aplicação excluída com sucesso.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir aplicação: {e}', 'danger')
    return redirect(url_for('admin.gerenciar_aplicacoes', produto_id=produto_id))

@admin_bp.route('/gerenciar_usuarios')
def gerenciar_usuarios():
    usuarios = User.query.order_by(User.id).all()
    return render_template('gerenciar_usuarios.html', usuarios=usuarios)

@admin_bp.route('/adicionar_usuario', methods=['POST'])
def adicionar_usuario():
    username = request.form.get('username')
    password = request.form.get('password')

    if User.query.filter_by(username=username).first():
        flash(f'O nome de usuário "{username}" já existe.', 'danger')
    else:
        new_user = User(username=username, is_admin=request.form.get('is_admin') == 'on')
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        flash(f'Usuário "{username}" criado com sucesso!', 'success')
    
    return redirect(url_for('admin.gerenciar_usuarios'))

@admin_bp.route('/excluir_usuario/<int:user_id>', methods=['POST'])
def excluir_usuario(user_id):
    user_to_delete = db.session.get(User, user_id)
    if user_to_delete and user_to_delete.id != current_user.id and user_to_delete.username != 'admin': # type: ignore
        db.session.delete(user_to_delete)
        db.session.commit()
        flash(f'Usuário "{user_to_delete.username}" excluído com sucesso.', 'success')
    else:
        flash('Não é possível excluir este usuário (você mesmo, ou o admin principal).', 'danger')
    return redirect(url_for('admin.gerenciar_usuarios'))

@admin_bp.route('/mudar_senha_usuario/<int:user_id>', methods=['POST'])
def mudar_senha_usuario(user_id):
    user_to_update = db.session.get(User, user_id)
    new_password = request.form.get('new_password')
    if user_to_update and new_password:
        user_to_update.set_password(new_password)
        db.session.commit()
        flash(f'Senha do usuário "{user_to_update.username}" alterada com sucesso.', 'success')
    else:
        flash('Não foi possível alterar a senha.', 'danger')
    return redirect(url_for('admin.gerenciar_usuarios'))

@admin_bp.route('/configuracoes', methods=['GET', 'POST'])
def configuracoes():
    config = carregar_config_aparencia()

    if request.method == 'POST':
        config['cor_principal'] = request.form.get('cor_principal', '#ff6600')

        if 'logo' in request.files:
            file = request.files['logo']
            if file and file.filename != '' and allowed_file(file.filename):
                logo_filename = "logo" + os.path.splitext(file.filename)[1]
                file.save(os.path.join(APP_DATA_PATH, 'uploads', logo_filename))
                config['logo_path'] = logo_filename
        
        salvar_config_aparencia(config)
        flash('Configurações de aparência salvas com sucesso!', 'success')
        return redirect(url_for('admin.configuracoes'))

    return render_template('configuracoes.html', config=config)

@admin_bp.route('/tarefas', methods=['GET'])
def pagina_tarefas():
    """Exibe a página para executar tarefas de importação e vinculação."""
    return render_template('tarefas.html', task_status=TASK_STATUS)

@admin_bp.route('/tarefas/status', methods=['GET'])
def status_tarefa():
    """Endpoint AJAX para obter o status da tarefa atual."""
    return jsonify(TASK_STATUS)

def _run_task_in_background(command_args, log_file_path):
    """Função genérica para executar um comando CLI em um subprocesso."""
    global TASK_STATUS
    try:
        # Redireciona a saída padrão e de erro para um arquivo de log (modo binário para evitar problemas de encoding)
        # O processo filho escreverá bytes brutos; ao ler o log, o leitor poderá tentar decodificar com utf-8 e
        # fazer fallback para latin-1 se necessário.
        with open(log_file_path, 'wb') as log_file:
            # Encontra o caminho para o executável python do ambiente virtual
            python_executable = sys.executable
            process = subprocess.Popen(
                [python_executable, 'run.py'] + command_args,
                stdout=log_file,
                stderr=subprocess.STDOUT
            )
            process.wait() # Espera o processo terminar

        # Lê o log para o status final (tenta decodificar em utf-8 com fallback)
        output = ''
        try:
            with open(log_file_path, 'rb') as log_file:
                data = log_file.read()
            try:
                output = data.decode('utf-8')
            except Exception:
                output = data.decode('latin-1', errors='replace')
        except Exception as e:
            output = f"(não foi possível ler o arquivo de log: {e})"

        if process.returncode == 0:
            TASK_STATUS['status'] = f"Concluído com sucesso às {datetime.now().strftime('%H:%M:%S')}"
        else:
            TASK_STATUS['status'] = f"Falhou às {datetime.now().strftime('%H:%M:%S')}"
        
        TASK_STATUS['output'] = output

    except Exception as e:
        TASK_STATUS['status'] = "Erro crítico ao iniciar a tarefa."
        TASK_STATUS['output'] = str(e)

@admin_bp.route('/tarefas/importar_csv', methods=['POST'])
def tarefa_importar_csv():
    global TASK_STATUS
    if TASK_STATUS['status'].startswith('Executando'):
        flash('Uma tarefa já está em execução. Aguarde a sua conclusão.', 'warning')
        return redirect(url_for('admin.pagina_tarefas'))

    if 'csv_file' not in request.files or request.files['csv_file'].filename == '':
        flash('Nenhum arquivo CSV foi enviado.', 'danger')
        return redirect(url_for('admin.pagina_tarefas'))

    file = request.files['csv_file']
    if not file.filename.endswith('.csv'):
        flash('Arquivo inválido. Por favor, envie um arquivo .csv.', 'danger')
        return redirect(url_for('admin.pagina_tarefas'))

    temp_csv_path = os.path.join(APP_DATA_PATH, secure_filename(f"import_{datetime.now().strftime('%Y%m%d%H%M%S')}.csv"))
    file.save(temp_csv_path)

    TASK_STATUS = {"status": "Executando: Importação de CSV...", "output": "Iniciando..."}
    log_file = os.path.join(APP_DATA_PATH, 'task_import.log')
    thread = threading.Thread(target=_run_task_in_background, args=(['import-csv', temp_csv_path], log_file))
    thread.start()

    flash('A importação foi iniciada em segundo plano.', 'info')
    return redirect(url_for('admin.pagina_tarefas'))

@admin_bp.route('/tarefas/vincular_imagens', methods=['POST'])
def tarefa_vincular_imagens():
    global TASK_STATUS
    if TASK_STATUS['status'].startswith('Executando'):
        flash('Uma tarefa já está em execução. Aguarde a sua conclusão.', 'warning')
        return redirect(url_for('admin.pagina_tarefas'))

    TASK_STATUS = {"status": "Executando: Vinculação de Imagens...", "output": "Iniciando..."}
    log_file = os.path.join(APP_DATA_PATH, 'task_link_images.log')
    thread = threading.Thread(target=_run_task_in_background, args=(['link-images'], log_file))
    thread.start()

    flash('A vinculação de imagens foi iniciada em segundo plano.', 'info')
    return redirect(url_for('admin.pagina_tarefas'))

@admin_bp.route('/backup')
def backup():
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    backup_filename = f"backup_catalogo_{timestamp}"
    temp_dir = os.getenv('TEMP', '/tmp')
    backup_zip_path = os.path.join(temp_dir, f"{backup_filename}.zip")
    source_db_path = os.path.join(APP_DATA_PATH, "catalogo.db")

    try:
        with zipfile.ZipFile(backup_zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            if os.path.exists(source_db_path):
                import sqlite3
                bck_conn = sqlite3.connect(':memory:')
                src_conn = sqlite3.connect(f'file:{source_db_path}?mode=ro', uri=True)
                src_conn.backup(bck_conn)
                db_dump = "\n".join(bck_conn.iterdump())
                zf.writestr('catalogo.db.sql', db_dump.encode('utf-8'))
                src_conn.close()
                bck_conn.close()

            for root, _, files in os.walk(APP_DATA_PATH):
                for file in files:
                    if file.startswith('catalogo.db'): continue
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, APP_DATA_PATH)
                    zf.write(file_path, arcname)

        return send_from_directory(temp_dir, f"{backup_filename}.zip", as_attachment=True)

    except Exception as e:
        flash(f"Erro ao criar o backup: {e}", "danger")
        print(f"Erro detalhado no backup: {e}")
        return redirect(url_for('admin.configuracoes'))

@admin_bp.route('/restaurar', methods=['POST'])
def restaurar():
    if 'backup_file' not in request.files:
        flash('Nenhum arquivo de backup foi enviado.', 'danger')
        return redirect(url_for('admin.configuracoes'))

    file = request.files['backup_file']
    if file.filename == '' or not file.filename.endswith('.zip'):
        flash('Arquivo inválido. Por favor, envie um arquivo .zip.', 'danger')
        return redirect(url_for('admin.configuracoes'))

    restore_filepath = os.path.join(APP_DATA_PATH, "backup_para_restaurar.zip")
    file.save(restore_filepath)

    is_sql_backup = False
    with zipfile.ZipFile(restore_filepath, 'r') as zf:
        if 'catalogo.db.sql' in zf.namelist():
            is_sql_backup = True

    if is_sql_backup:
        try:
            with zipfile.ZipFile(restore_filepath, 'r') as zf:
                zf.extractall(APP_DATA_PATH)

            import sqlite3
            db_path = os.path.join(APP_DATA_PATH, "catalogo.db")
            sql_path = os.path.join(APP_DATA_PATH, "catalogo.db.sql")
            if os.path.exists(db_path): os.remove(db_path)
            
            conn = sqlite3.connect(db_path)
            with open(sql_path, 'r', encoding='utf-8') as f:
                conn.executescript(f.read())
            conn.close()
            
            os.remove(sql_path)
            os.remove(restore_filepath)
            flash("Restauração concluída com sucesso! A página será recarregada.", "success")
            return redirect(url_for('admin.configuracoes'))
        except Exception as e:
            flash(f"Erro ao restaurar o backup: {e}", "danger")
            return redirect(url_for('admin.configuracoes'))
    else:
        restart_trigger_file = os.path.join(APP_DATA_PATH, 'RESTART_REQUIRED')
        with open(restart_trigger_file, 'w') as f: f.write('restart')
        return render_template('reiniciando.html')

@admin_bp.route('/exportar/csv')
def exportar_csv():
    # Reutiliza os mesmos parâmetros da busca
    args = request.args.copy()
    query = _build_search_query(
        args.get('termo', ''), args.get('codigo_produto', ''), args.get('montadora', ''),
        args.get('aplicacao', ''), args.get('grupo', ''), args.get('medidas', '')
    )
    resultados = query.options(db.joinedload(Produto.aplicacoes)).all()

    def generate():
        yield 'codigo,nome,grupo,fornecedor,conversoes,medidas,observacoes,aplicacoes_json\n'
        for produto in resultados:
            aplicacoes_list = [{"veiculo": app.veiculo, "ano": app.ano, "motor": app.motor, "conf_mtr": app.conf_mtr, "montadora": app.montadora} for app in produto.aplicacoes]
            aplicacoes_json = json.dumps(aplicacoes_list, ensure_ascii=False)
            row_data = [
                produto.codigo or "", produto.nome or "", produto.grupo or "",
                produto.fornecedor or "", produto.conversoes or "", produto.medidas or "",
                produto.observacoes or "", aplicacoes_json
            ]
            # Escapa aspas duplas dentro dos campos e envolve cada campo com aspas
            row = ','.join([f'"{str(field).replace("\"", "\"\"")}"' for field in row_data]) + '\n'
            yield row

    return Response(generate(), mimetype='text/csv', headers={"Content-disposition": "attachment; filename=export_pecas.csv"})

# --- Rotas de API (para AJAX) ---

@main_bp.route('/api/check_codigo')
@login_required
def check_codigo():
    """Verifica se um código de produto já existe no banco de dados (via AJAX)."""
    codigo = request.args.get('codigo', type=str)
    produto_id = request.args.get('produto_id', type=int)

    if not codigo:
        return {"exists": False}

    query = Produto.query.filter(Produto.codigo == codigo)
    if produto_id is not None:
        query = query.filter(Produto.id != int(produto_id))

    produto_existente = query.first()
    return {"exists": bool(produto_existente), "nome": getattr(produto_existente, 'nome', None)}

@main_bp.route('/api/buscar_pecas_similares')
@login_required
def buscar_pecas_similares():
    """Busca peças para o campo de autocompletar de similares."""
    termo_busca = request.args.get('q', '').strip()
    produto_atual_id = request.args.get('exclude_id', type=int)

    if not termo_busca or len(termo_busca) < 2:
        return {"items": []}

    query = Produto.query.filter(or_(Produto.codigo.ilike(f'%{termo_busca}%'), Produto.nome.ilike(f'%{termo_busca}%')))
    if produto_atual_id:
        query = query.filter(Produto.id != produto_atual_id)

    resultados = query.limit(10).all()
    items = [{"id": p.id, "codigo": p.codigo, "nome": p.nome} for p in resultados]
    return {"items": items}

@main_bp.route('/api/get_montadora')
@login_required
def get_montadora_for_veiculo():
    """Busca a montadora mais provável para um determinado veículo."""
    veiculo = request.args.get('veiculo', '').strip().upper()
    if not veiculo:
        return {"montadora": None}

    aplicacao = Aplicacao.query.filter(Aplicacao.veiculo.ilike(veiculo)).order_by(Aplicacao.id.desc()).first()
    return {"montadora": aplicacao.montadora if aplicacao else None}